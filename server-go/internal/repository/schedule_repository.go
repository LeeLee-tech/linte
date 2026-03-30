package repository

import (
	"linte/server-go/internal/model"

	"gorm.io/gorm"
)

type ScheduleRepository struct {
	db *gorm.DB
}

func NewScheduleRepository(db *gorm.DB) *ScheduleRepository {
	return &ScheduleRepository{db: db}
}

func (r *ScheduleRepository) Create(schedule *model.Schedule) error {
	return r.db.Create(schedule).Error
}

func (r *ScheduleRepository) ListByUserID(userID string) ([]model.Schedule, error) {
	var schedules []model.Schedule
	err := r.db.Where("user_id = ?", userID).Order("created_at DESC").Find(&schedules).Error
	return schedules, err
}

func (r *ScheduleRepository) FindByIDAndUserID(scheduleID, userID string) (*model.Schedule, error) {
	var schedule model.Schedule
	err := r.db.Where("id = ? AND user_id = ?", scheduleID, userID).First(&schedule).Error
	if err != nil {
		return nil, err
	}
	return &schedule, nil
}

func (r *ScheduleRepository) ListByUserIDs(userIDs []string) ([]model.Schedule, error) {
	var schedules []model.Schedule
	err := r.db.Where("user_id IN ?", userIDs).Find(&schedules).Error
	return schedules, err
}

func (r *ScheduleRepository) Delete(schedule *model.Schedule) error {
	return r.db.Delete(schedule).Error
}

func (r *ScheduleRepository) Update(schedule *model.Schedule) error {
	return r.db.Save(schedule).Error
}
