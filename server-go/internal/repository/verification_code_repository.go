package repository

import (
	"linte/server-go/internal/model"
	"time"

	"gorm.io/gorm"
)

type VerificationCodeRepository struct {
	db *gorm.DB
}

func NewVerificationCodeRepository(db *gorm.DB) *VerificationCodeRepository {
	return &VerificationCodeRepository{db: db}
}

func (r *VerificationCodeRepository) DeleteByEmailAndType(email, codeType string) error {
	return r.db.Where("email = ? AND type = ?", email, codeType).Delete(&model.VerificationCode{}).Error
}

func (r *VerificationCodeRepository) Create(code *model.VerificationCode) error {
	return r.db.Create(code).Error
}

func (r *VerificationCodeRepository) FindValid(email, code, codeType string, now time.Time) (*model.VerificationCode, error) {
	var verificationCode model.VerificationCode
	err := r.db.Where(
		"email = ? AND code = ? AND type = ? AND is_used = ? AND expires_at > ?",
		email,
		code,
		codeType,
		false,
		now,
	).First(&verificationCode).Error
	if err != nil {
		return nil, err
	}
	return &verificationCode, nil
}

func (r *VerificationCodeRepository) Update(code *model.VerificationCode) error {
	return r.db.Save(code).Error
}

func (r *VerificationCodeRepository) FindLatestByEmailAndType(email, codeType string) (*model.VerificationCode, error) {
	var verificationCode model.VerificationCode
	err := r.db.Where("email = ? AND type = ?", email, codeType).Order("created_at DESC").First(&verificationCode).Error
	if err != nil {
		return nil, err
	}
	return &verificationCode, nil
}
