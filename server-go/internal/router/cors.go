package router

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

func cors(origins []string) gin.HandlerFunc {
	allowAll := len(origins) == 1 && origins[0] == "*"

	return func(c *gin.Context) {
		origin := c.GetHeader("Origin")
		if allowAll {
			c.Writer.Header().Set("Access-Control-Allow-Origin", "*")
		} else if origin != "" && contains(origins, origin) {
			c.Writer.Header().Set("Access-Control-Allow-Origin", origin)
			c.Writer.Header().Set("Vary", "Origin")
		}

		c.Writer.Header().Set("Access-Control-Allow-Headers", "Authorization, Content-Type")
		c.Writer.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		c.Writer.Header().Set("Access-Control-Allow-Credentials", "true")

		if c.Request.Method == http.MethodOptions {
			c.AbortWithStatus(http.StatusNoContent)
			return
		}

		c.Next()
	}
}

func contains(items []string, target string) bool {
	for _, item := range items {
		if item == target {
			return true
		}
	}
	return false
}
