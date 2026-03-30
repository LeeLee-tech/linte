package service

import (
	"crypto/rand"
	"errors"
	"fmt"
	"math/big"
	"strings"
	"time"

	"linte/server-go/internal/model"
	"linte/server-go/internal/pkg/jwtx"
	"linte/server-go/internal/pkg/mailer"
	"linte/server-go/internal/pkg/password"
	"linte/server-go/internal/repository"

	"github.com/google/uuid"
	"gorm.io/gorm"
)

type AuthService struct {
	users      *repository.UserRepository
	codes      *repository.VerificationCodeRepository
	mailer     mailer.Mailer
	jwtManager *jwtx.Manager
	codeTTL    time.Duration
	cooldown   time.Duration
	exposeCode bool
}

type AuthResult struct {
	UserID      string `json:"user_id"`
	Email       string `json:"email"`
	AccessToken string `json:"access_token"`
	TokenType   string `json:"token_type"`
}

type SendCodeResult struct {
	Message           string `json:"msg"`
	DebugCode         string `json:"debug_code,omitempty"`
	RetryAfterSeconds int    `json:"retry_after_seconds,omitempty"`
}

type AppError struct {
	Code             string
	Message          string
	RetryAfterSecond int
}

func (e *AppError) Error() string {
	return e.Message
}

func NewAuthService(users *repository.UserRepository, codes *repository.VerificationCodeRepository, mailer mailer.Mailer, jwtManager *jwtx.Manager, codeTTL time.Duration, cooldown time.Duration, exposeCode bool) *AuthService {
	return &AuthService{
		users:      users,
		codes:      codes,
		mailer:     mailer,
		jwtManager: jwtManager,
		codeTTL:    codeTTL,
		cooldown:   cooldown,
		exposeCode: exposeCode,
	}
}

func (s *AuthService) SendCode(email, codeType string) (*SendCodeResult, error) {
	codeType = strings.TrimSpace(codeType)
	if codeType != "register" && codeType != "reset" {
		return nil, &AppError{Code: "bad_request", Message: "invalid code type"}
	}

	latestCode, err := s.codes.FindLatestByEmailAndType(email, codeType)
	if err == nil && s.cooldown > 0 {
		elapsed := time.Since(latestCode.CreatedAt)
		if elapsed < s.cooldown {
			retryAfter := int((s.cooldown - elapsed).Seconds())
			if retryAfter < 1 {
				retryAfter = 1
			}
			return nil, &AppError{
				Code:             "rate_limited",
				Message:          "verification code requested too frequently",
				RetryAfterSecond: retryAfter,
			}
		}
	} else if err != nil && !errors.Is(err, gorm.ErrRecordNotFound) {
		return nil, err
	}

	code, err := generateNumericCode(6)
	if err != nil {
		return nil, err
	}

	if err := s.codes.DeleteByEmailAndType(email, codeType); err != nil {
		return nil, err
	}
	if err := s.codes.Create(&model.VerificationCode{
		Email:     email,
		Code:      code,
		Type:      codeType,
		ExpiresAt: time.Now().UTC().Add(s.codeTTL),
		IsUsed:    false,
	}); err != nil {
		return nil, err
	}

	if err := s.mailer.SendVerificationCode(email, code); err != nil {
		return nil, &AppError{Code: "mailer_failed", Message: "failed to send verification email"}
	}

	result := &SendCodeResult{Message: "verification code generated"}
	if s.exposeCode && !s.mailer.IsConfigured() {
		result.Message = "verification code generated in debug mode"
		result.DebugCode = code
	}
	return result, nil
}

func (s *AuthService) Register(email, rawPassword, code string) (*AuthResult, error) {
	codeRecord, err := s.codes.FindValid(email, code, "register", time.Now().UTC())
	if err != nil {
		if err == gorm.ErrRecordNotFound {
			return nil, fmt.Errorf("verification code is invalid or expired")
		}
		return nil, err
	}

	if _, err := s.users.FindByEmail(email); err == nil {
		return nil, fmt.Errorf("email already registered")
	} else if err != gorm.ErrRecordNotFound {
		return nil, err
	}

	hashedPassword, err := password.Hash(rawPassword)
	if err != nil {
		return nil, err
	}

	user := &model.User{
		UserID:         "user_" + uuid.NewString(),
		Email:          email,
		HashedPassword: hashedPassword,
	}
	if err := s.users.Create(user); err != nil {
		return nil, err
	}

	codeRecord.IsUsed = true
	if err := s.codes.Update(codeRecord); err != nil {
		return nil, err
	}

	return s.issueToken(user)
}

func (s *AuthService) Login(email, rawPassword string) (*AuthResult, error) {
	user, err := s.users.FindByEmail(email)
	if err != nil {
		if err == gorm.ErrRecordNotFound {
			return nil, fmt.Errorf("user not found")
		}
		return nil, err
	}

	if !password.Verify(rawPassword, user.HashedPassword) {
		return nil, fmt.Errorf("invalid email or password")
	}

	return s.issueToken(user)
}

func (s *AuthService) ResetPassword(email, newPassword, code string) error {
	codeRecord, err := s.codes.FindValid(email, code, "reset", time.Now().UTC())
	if err != nil {
		if err == gorm.ErrRecordNotFound {
			return fmt.Errorf("verification code is invalid or expired")
		}
		return err
	}

	user, err := s.users.FindByEmail(email)
	if err != nil {
		if err == gorm.ErrRecordNotFound {
			return fmt.Errorf("user not found")
		}
		return err
	}

	hashedPassword, err := password.Hash(newPassword)
	if err != nil {
		return err
	}

	user.HashedPassword = hashedPassword
	if err := s.users.Update(user); err != nil {
		return err
	}

	codeRecord.IsUsed = true
	return s.codes.Update(codeRecord)
}

func (s *AuthService) issueToken(user *model.User) (*AuthResult, error) {
	token, err := s.jwtManager.Generate(user.UserID, user.Email)
	if err != nil {
		return nil, err
	}
	return &AuthResult{
		UserID:      user.UserID,
		Email:       user.Email,
		AccessToken: token,
		TokenType:   "bearer",
	}, nil
}

func generateNumericCode(length int) (string, error) {
	var builder strings.Builder
	for i := 0; i < length; i++ {
		number, err := rand.Int(rand.Reader, big.NewInt(10))
		if err != nil {
			return "", err
		}
		builder.WriteByte(byte(number.Int64()) + '0')
	}
	return builder.String(), nil
}
