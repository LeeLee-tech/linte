package jwtx

import (
	"fmt"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

type Manager struct {
	secret []byte
	ttl    time.Duration
}

type Claims struct {
	Email string `json:"email"`
	jwt.RegisteredClaims
}

func New(secret string, ttl time.Duration) *Manager {
	return &Manager{
		secret: []byte(secret),
		ttl:    ttl,
	}
}

func (m *Manager) Generate(userID, email string) (string, error) {
	now := time.Now().UTC()
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, Claims{
		Email: email,
		RegisteredClaims: jwt.RegisteredClaims{
			Subject:   userID,
			ExpiresAt: jwt.NewNumericDate(now.Add(m.ttl)),
			IssuedAt:  jwt.NewNumericDate(now),
		},
	})

	return token.SignedString(m.secret)
}

func (m *Manager) Parse(tokenString string) (*Claims, error) {
	token, err := jwt.ParseWithClaims(tokenString, &Claims{}, func(token *jwt.Token) (any, error) {
		if token.Method != jwt.SigningMethodHS256 {
			return nil, fmt.Errorf("unexpected signing method")
		}
		return m.secret, nil
	})
	if err != nil {
		return nil, err
	}

	claims, ok := token.Claims.(*Claims)
	if !ok || !token.Valid {
		return nil, fmt.Errorf("invalid token")
	}
	return claims, nil
}
