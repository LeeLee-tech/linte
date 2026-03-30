package middleware

import (
	"net/http"
	"strings"

	"linte/server-go/internal/pkg/jwtx"

	"github.com/gin-gonic/gin"
)

const (
	ContextUserIDKey = "current_user_id"
	ContextEmailKey  = "current_user_email"
)

func Auth(jwtManager *jwtx.Manager) gin.HandlerFunc {
	return func(c *gin.Context) {
		header := strings.TrimSpace(c.GetHeader("Authorization"))
		if header == "" || !strings.HasPrefix(strings.ToLower(header), "bearer ") {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "missing bearer token"})
			return
		}

		tokenString := strings.TrimSpace(header[7:])
		claims, err := jwtManager.Parse(tokenString)
		if err != nil {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "invalid token"})
			return
		}

		c.Set(ContextUserIDKey, claims.Subject)
		c.Set(ContextEmailKey, claims.Email)
		c.Next()
	}
}

func CurrentUserID(c *gin.Context) string {
	value, _ := c.Get(ContextUserIDKey)
	userID, _ := value.(string)
	return userID
}
