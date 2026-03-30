package service

import (
	"fmt"
	"math"
	"sort"
	"time"

	"linte/server-go/internal/model"
	"linte/server-go/internal/pkg/matcher"
	"linte/server-go/internal/repository"

	"gorm.io/gorm"
)

type MatchService struct {
	users               *repository.UserRepository
	schedules           *repository.ScheduleRepository
	engine              matcher.Matcher
	nearbyActiveMinutes int
	maxMatchResults     int
}

type MatchInput struct {
	ID        string `json:"id"`
	Title     string `json:"title"`
	TimeRange string `json:"time_range"`
	Content   string `json:"content"`
}

type NearbyMatch struct {
	TargetUserID      string  `json:"target_user_id"`
	TargetEmail       string  `json:"target_email"`
	DistanceMeters    float64 `json:"distance_m"`
	MyScheduleTitle   string  `json:"my_schedule_title"`
	MatchedScheduleID string  `json:"matched_schedule_id"`
	MatchedTime       string  `json:"matched_time"`
	MatchedContent    string  `json:"matched_content"`
	Score             float64 `json:"score"`
	ScoreLevel        string  `json:"score_level"`
}

func NewMatchService(users *repository.UserRepository, schedules *repository.ScheduleRepository, engine matcher.Matcher, nearbyActiveMinutes int, maxMatchResults int) *MatchService {
	return &MatchService{
		users:               users,
		schedules:           schedules,
		engine:              engine,
		nearbyActiveMinutes: nearbyActiveMinutes,
		maxMatchResults:     maxMatchResults,
	}
}

func (s *MatchService) Match(profile MatchInput, candidates []MatchInput) []matcher.Result {
	engineCandidates := make([]matcher.Input, 0, len(candidates))
	for i, candidate := range candidates {
		id := candidate.ID
		if id == "" {
			id = fmt.Sprintf("c%d", i)
		}
		engineCandidates = append(engineCandidates, matcher.Input{
			ID:        id,
			TimeRange: candidate.TimeRange,
			Content:   candidate.Content,
		})
	}

	return s.engine.Match(matcher.Input{
		ID:        profile.ID,
		TimeRange: profile.TimeRange,
		Content:   profile.Content,
	}, engineCandidates)
}

func (s *MatchService) UpdateLocation(userID string, latitude, longitude float64) (*model.User, error) {
	user, err := s.users.FindByID(userID)
	if err != nil {
		if err == gorm.ErrRecordNotFound {
			return nil, fmt.Errorf("user not found")
		}
		return nil, err
	}

	now := time.Now().UTC()
	user.Latitude = &latitude
	user.Longitude = &longitude
	user.LastLocationUpdate = &now
	if err := s.users.Update(user); err != nil {
		return nil, err
	}
	return user, nil
}

func (s *MatchService) FindNearbyComprehensive(userID string, latitude, longitude float64, radiusMeters int, mySchedules []MatchInput) ([]NearbyMatch, int, error) {
	if _, err := s.UpdateLocation(userID, latitude, longitude); err != nil {
		return nil, 0, err
	}

	threshold := time.Now().UTC().Add(-time.Duration(s.nearbyActiveMinutes) * time.Minute)
	users, err := s.users.FindNearbyActive(userID, threshold)
	if err != nil {
		return nil, 0, err
	}

	type candidateUser struct {
		user     model.User
		distance float64
	}

	validUsers := make([]candidateUser, 0)
	for _, user := range users {
		if user.Latitude == nil || user.Longitude == nil {
			continue
		}
		distance := haversineMeters(latitude, longitude, *user.Latitude, *user.Longitude)
		if distance <= float64(radiusMeters) {
			validUsers = append(validUsers, candidateUser{user: user, distance: distance})
		}
	}

	if len(validUsers) == 0 {
		return []NearbyMatch{}, 0, nil
	}

	userIDs := make([]string, 0, len(validUsers))
	for _, user := range validUsers {
		userIDs = append(userIDs, user.user.UserID)
	}

	targetSchedules, err := s.schedules.ListByUserIDs(userIDs)
	if err != nil {
		return nil, 0, err
	}

	schedulesByUser := make(map[string][]model.Schedule)
	for _, schedule := range targetSchedules {
		schedulesByUser[schedule.UserID] = append(schedulesByUser[schedule.UserID], schedule)
	}

	matches := make([]NearbyMatch, 0)
	for _, nearbyUser := range validUsers {
		candidateSchedules := schedulesByUser[nearbyUser.user.UserID]
		if len(candidateSchedules) == 0 {
			continue
		}

		engineCandidates := make([]matcher.Input, 0, len(candidateSchedules))
		for _, schedule := range candidateSchedules {
			engineCandidates = append(engineCandidates, matcher.Input{
				ID:        schedule.ID,
				TimeRange: schedule.TimeRange,
				Content:   schedule.Content,
			})
		}

		for _, mySchedule := range mySchedules {
			results := s.engine.Match(matcher.Input{
				ID:        mySchedule.ID,
				TimeRange: mySchedule.TimeRange,
				Content:   mySchedule.Content,
			}, engineCandidates)
			if len(results) == 0 {
				continue
			}

			best := results[0]
			matches = append(matches, NearbyMatch{
				TargetUserID:      nearbyUser.user.UserID,
				TargetEmail:       nearbyUser.user.Email,
				DistanceMeters:    roundMatch(nearbyUser.distance, 1),
				MyScheduleTitle:   mySchedule.Title,
				MatchedScheduleID: best.ID,
				MatchedTime:       best.Time,
				MatchedContent:    best.Content,
				Score:             best.Score,
				ScoreLevel:        best.Level,
			})
		}
	}

	sort.Slice(matches, func(i, j int) bool {
		if matches[i].DistanceMeters == matches[j].DistanceMeters {
			return matches[i].Score > matches[j].Score
		}
		return matches[i].DistanceMeters < matches[j].DistanceMeters
	})

	if len(matches) > s.maxMatchResults {
		matches = matches[:s.maxMatchResults]
	}
	return matches, len(validUsers), nil
}

func haversineMeters(lat1, lng1, lat2, lng2 float64) float64 {
	rad := func(value float64) float64 { return value * math.Pi / 180 }
	dLat := rad(lat2 - lat1)
	dLng := rad(lng2 - lng1)
	a := math.Sin(dLat/2)*math.Sin(dLat/2) + math.Cos(rad(lat1))*math.Cos(rad(lat2))*math.Sin(dLng/2)*math.Sin(dLng/2)
	c := 2 * math.Asin(math.Sqrt(a))
	return 6371000 * c
}

func roundMatch(value float64, precision int) float64 {
	pow := math.Pow(10, float64(precision))
	return math.Round(value*pow) / pow
}
