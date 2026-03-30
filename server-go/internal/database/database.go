package database

import (
	"fmt"

	"linte/server-go/internal/model"

	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
)

func New(databaseURL string) (*gorm.DB, error) {
	db, err := gorm.Open(sqlite.Open(databaseURL), &gorm.Config{})
	if err != nil {
		return nil, fmt.Errorf("open sqlite: %w", err)
	}

	if err := db.AutoMigrate(&model.User{}, &model.VerificationCode{}, &model.Schedule{}); err != nil {
		return nil, fmt.Errorf("auto migrate: %w", err)
	}

	return db, nil
}
