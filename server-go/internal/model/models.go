package model

import "time"

type User struct {
	UserID             string     `gorm:"primaryKey;size:64" json:"user_id"`
	Email              string     `gorm:"uniqueIndex;size:255;not null" json:"email"`
	HashedPassword     string     `gorm:"size:255;not null" json:"-"`
	CreatedAt          time.Time  `json:"created_at"`
	Latitude           *float64   `json:"latitude,omitempty"`
	Longitude          *float64   `json:"longitude,omitempty"`
	LastLocationUpdate *time.Time `json:"last_location_update,omitempty"`
	Schedules          []Schedule `gorm:"foreignKey:UserID;references:UserID" json:"-"`
}

type VerificationCode struct {
	ID        uint      `gorm:"primaryKey" json:"id"`
	Email     string    `gorm:"index;size:255;not null" json:"email"`
	Code      string    `gorm:"size:16;not null" json:"code"`
	Type      string    `gorm:"size:32;not null" json:"type"`
	ExpiresAt time.Time `gorm:"not null" json:"expires_at"`
	IsUsed    bool      `gorm:"not null;default:false" json:"is_used"`
	CreatedAt time.Time `json:"created_at"`
}

type Schedule struct {
	ID        string    `gorm:"primaryKey;size:64" json:"id"`
	UserID    string    `gorm:"index;size:64;not null" json:"user_id"`
	Title     string    `gorm:"size:255;not null" json:"title"`
	Date      string    `gorm:"size:32;not null" json:"date"`
	TimeRange string    `gorm:"size:64;not null" json:"time_range"`
	Location  string    `gorm:"size:255" json:"location"`
	Content   string    `gorm:"type:text;not null" json:"content"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}
