package service

import (
	"fmt"
	"strings"

	"linte/server-go/internal/model"
	"linte/server-go/internal/repository"

	"github.com/google/uuid"
	"gorm.io/gorm"
)

type ScheduleService struct {
	schedules *repository.ScheduleRepository
}

func NewScheduleService(schedules *repository.ScheduleRepository) *ScheduleService {
	return &ScheduleService{schedules: schedules}
}

func (s *ScheduleService) Create(userID, title, timeRange, content string) (*model.Schedule, error) {
	schedule := &model.Schedule{
		ID:        "sched_" + uuid.NewString(),
		UserID:    userID,
		Title:     strings.TrimSpace(title),
		Date:      "",
		TimeRange: strings.TrimSpace(timeRange),
		Location:  "",
		Content:   strings.TrimSpace(content),
	}
	if err := s.schedules.Create(schedule); err != nil {
		return nil, err
	}
	return schedule, nil
}

func (s *ScheduleService) CreateDetailed(userID, title, date, timeRange, location, content string) (*model.Schedule, error) {
	schedule := &model.Schedule{
		ID:        "sched_" + uuid.NewString(),
		UserID:    userID,
		Title:     strings.TrimSpace(title),
		Date:      strings.TrimSpace(date),
		TimeRange: strings.TrimSpace(timeRange),
		Location:  strings.TrimSpace(location),
		Content:   strings.TrimSpace(content),
	}
	if schedule.Content == "" {
		schedule.Content = strings.TrimSpace(title + " " + location)
	}
	if err := s.schedules.Create(schedule); err != nil {
		return nil, err
	}
	return schedule, nil
}

func (s *ScheduleService) List(userID string) ([]model.Schedule, error) {
	return s.schedules.ListByUserID(userID)
}

func (s *ScheduleService) Delete(userID, scheduleID string) error {
	schedule, err := s.schedules.FindByIDAndUserID(scheduleID, userID)
	if err != nil {
		if err == gorm.ErrRecordNotFound {
			return fmt.Errorf("schedule not found")
		}
		return err
	}
	return s.schedules.Delete(schedule)
}

func (s *ScheduleService) Update(userID, scheduleID, title, date, timeRange, location, content string) (*model.Schedule, error) {
	schedule, err := s.schedules.FindByIDAndUserID(scheduleID, userID)
	if err != nil {
		if err == gorm.ErrRecordNotFound {
			return nil, fmt.Errorf("schedule not found")
		}
		return nil, err
	}

	schedule.Title = strings.TrimSpace(title)
	schedule.Date = strings.TrimSpace(date)
	schedule.TimeRange = strings.TrimSpace(timeRange)
	schedule.Location = strings.TrimSpace(location)
	schedule.Content = strings.TrimSpace(content)
	if schedule.Content == "" {
		schedule.Content = strings.TrimSpace(title + " " + location)
	}

	if err := s.schedules.Update(schedule); err != nil {
		return nil, err
	}
	return schedule, nil
}
