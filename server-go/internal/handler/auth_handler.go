package handler

import (
	"net/http"

	"linte/server-go/internal/service"

	"github.com/gin-gonic/gin"
)

type AuthHandler struct {
	auth *service.AuthService
}

type sendCodeRequest struct {
	Email string `json:"email" binding:"required,email"`
	Type  string `json:"type" binding:"required"`
}

type registerRequest struct {
	Email    string `json:"email" binding:"required,email"`
	Password string `json:"password" binding:"required"`
	Code     string `json:"code" binding:"required"`
}

type loginRequest struct {
	Email    string `json:"email" binding:"required,email"`
	Password string `json:"password" binding:"required"`
}

type resetPasswordRequest struct {
	Email       string `json:"email" binding:"required,email"`
	NewPassword string `json:"new_password" binding:"required"`
	Code        string `json:"code" binding:"required"`
}

func NewAuthHandler(auth *service.AuthService) *AuthHandler {
	return &AuthHandler{auth: auth}
}

func (h *AuthHandler) SendCode(c *gin.Context) {
	var req sendCodeRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	result, err := h.auth.SendCode(req.Email, req.Type)
	if err != nil {
		var appErr *service.AppError
		if ok := errorAs(err, &appErr); ok {
			switch appErr.Code {
			case "rate_limited":
				c.JSON(http.StatusTooManyRequests, gin.H{"error": appErr.Message, "retry_after_seconds": appErr.RetryAfterSecond})
			case "mailer_failed":
				c.JSON(http.StatusServiceUnavailable, gin.H{"error": appErr.Message})
			default:
				c.JSON(http.StatusBadRequest, gin.H{"error": appErr.Message})
			}
			return
		}
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, result)
}

func errorAs(err error, target **service.AppError) bool {
	appErr, ok := err.(*service.AppError)
	if !ok {
		return false
	}
	*target = appErr
	return true
}

func (h *AuthHandler) Register(c *gin.Context) {
	var req registerRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	result, err := h.auth.Register(req.Email, req.Password, req.Code)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, result)
}

func (h *AuthHandler) Login(c *gin.Context) {
	var req loginRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	result, err := h.auth.Login(req.Email, req.Password)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, result)
}

func (h *AuthHandler) ResetPassword(c *gin.Context) {
	var req resetPasswordRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if err := h.auth.ResetPassword(req.Email, req.NewPassword, req.Code); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"msg": "password reset successful"})
}
