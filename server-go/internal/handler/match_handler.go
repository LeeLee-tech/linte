package handler

import (
	"net/http"

	"linte/server-go/internal/middleware"
	"linte/server-go/internal/service"

	"github.com/gin-gonic/gin"
)

type MatchHandler struct {
	match *service.MatchService
}

type matchInput struct {
	ID        string `json:"id"`
	Title     string `json:"title"`
	TimeRange string `json:"time_range" binding:"required"`
	Content   string `json:"content" binding:"required"`
}

type matchRequest struct {
	MyProfile  matchInput   `json:"my_profile" binding:"required"`
	Candidates []matchInput `json:"candidates" binding:"required"`
}

type updateLocationRequest struct {
	Latitude  float64 `json:"latitude" binding:"required"`
	Longitude float64 `json:"longitude" binding:"required"`
}

type nearbyMatchRequest struct {
	Latitude     float64      `json:"latitude" binding:"required"`
	Longitude    float64      `json:"longitude" binding:"required"`
	RadiusMeters int          `json:"radius_meters"`
	MySchedules  []matchInput `json:"my_schedules" binding:"required"`
}

func NewMatchHandler(match *service.MatchService) *MatchHandler {
	return &MatchHandler{match: match}
}

func (h *MatchHandler) RunMatch(c *gin.Context) {
	var req matchRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	candidates := make([]service.MatchInput, 0, len(req.Candidates))
	for _, candidate := range req.Candidates {
		candidates = append(candidates, toServiceMatchInput(candidate))
	}

	results := h.match.Match(toServiceMatchInput(req.MyProfile), candidates)
	c.JSON(http.StatusOK, gin.H{"matches": results})
}

func (h *MatchHandler) UpdateLocation(c *gin.Context) {
	var req updateLocationRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	user, err := h.match.UpdateLocation(middleware.CurrentUserID(c), req.Latitude, req.Longitude)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"msg": "location updated", "time": user.LastLocationUpdate})
}

func (h *MatchHandler) FindNearbyComprehensive(c *gin.Context) {
	var req nearbyMatchRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	radius := req.RadiusMeters
	if radius <= 0 {
		radius = 200
	}

	mySchedules := make([]service.MatchInput, 0, len(req.MySchedules))
	for _, item := range req.MySchedules {
		mySchedules = append(mySchedules, toServiceMatchInput(item))
	}

	results, totalNearbyUsers, err := h.match.FindNearbyComprehensive(
		middleware.CurrentUserID(c),
		req.Latitude,
		req.Longitude,
		radius,
		mySchedules,
	)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if len(results) == 0 {
		c.JSON(http.StatusOK, gin.H{
			"msg":                "no active nearby users found",
			"total_nearby_users": totalNearbyUsers,
			"matches":            []any{},
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"msg":                "matching completed",
		"total_nearby_users": totalNearbyUsers,
		"matches":            results,
	})
}

func toServiceMatchInput(input matchInput) service.MatchInput {
	return service.MatchInput{
		ID:        input.ID,
		Title:     input.Title,
		TimeRange: input.TimeRange,
		Content:   input.Content,
	}
}
