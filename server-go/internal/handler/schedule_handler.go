package handler

import (
	"net/http"

	"linte/server-go/internal/middleware"
	"linte/server-go/internal/service"

	"github.com/gin-gonic/gin"
)

type ScheduleHandler struct {
	schedules *service.ScheduleService
}

type createScheduleRequest struct {
	Title     string `json:"title" binding:"required"`
	Date      string `json:"date" binding:"required"`
	TimeRange string `json:"time_range" binding:"required"`
	Location  string `json:"location"`
	Content   string `json:"content" binding:"required"`
}

type updateScheduleRequest struct {
	Title     string `json:"title" binding:"required"`
	Date      string `json:"date" binding:"required"`
	TimeRange string `json:"time_range" binding:"required"`
	Location  string `json:"location"`
	Content   string `json:"content" binding:"required"`
}

func NewScheduleHandler(schedules *service.ScheduleService) *ScheduleHandler {
	return &ScheduleHandler{schedules: schedules}
}

func (h *ScheduleHandler) Create(c *gin.Context) {
	var req createScheduleRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	schedule, err := h.schedules.CreateDetailed(middleware.CurrentUserID(c), req.Title, req.Date, req.TimeRange, req.Location, req.Content)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, schedule)
}

func (h *ScheduleHandler) List(c *gin.Context) {
	schedules, err := h.schedules.List(middleware.CurrentUserID(c))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, schedules)
}

func (h *ScheduleHandler) Delete(c *gin.Context) {
	scheduleID := c.Param("schedule_id")
	if err := h.schedules.Delete(middleware.CurrentUserID(c), scheduleID); err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"msg": "delete successful"})
}

func (h *ScheduleHandler) Update(c *gin.Context) {
	var req updateScheduleRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	schedule, err := h.schedules.Update(
		middleware.CurrentUserID(c),
		c.Param("schedule_id"),
		req.Title,
		req.Date,
		req.TimeRange,
		req.Location,
		req.Content,
	)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, schedule)
}
