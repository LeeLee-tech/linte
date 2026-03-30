package repository

import (
	"linte/server-go/internal/model"
	"time"

	"gorm.io/gorm"
)

type UserRepository struct {
	db *gorm.DB
}

func NewUserRepository(db *gorm.DB) *UserRepository {
	return &UserRepository{db: db}
}

func (r *UserRepository) Create(user *model.User) error {
	return r.db.Create(user).Error
}

func (r *UserRepository) FindByEmail(email string) (*model.User, error) {
	var user model.User
	err := r.db.Where("email = ?", email).First(&user).Error
	if err != nil {
		return nil, err
	}
	return &user, nil
}

func (r *UserRepository) FindByID(userID string) (*model.User, error) {
	var user model.User
	err := r.db.Where("user_id = ?", userID).First(&user).Error
	if err != nil {
		return nil, err
	}
	return &user, nil
}

func (r *UserRepository) Update(user *model.User) error {
	return r.db.Save(user).Error
}

func (r *UserRepository) FindNearbyActive(excludeUserID string, activeAfter time.Time) ([]model.User, error) {
	var users []model.User
	err := r.db.
		Where("user_id <> ?", excludeUserID).
		Where("latitude IS NOT NULL").
		Where("longitude IS NOT NULL").
		Where("last_location_update >= ?", activeAfter).
		Find(&users).Error
	return users, err
}
