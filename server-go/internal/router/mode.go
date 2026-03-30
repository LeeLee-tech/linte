package router

import "github.com/gin-gonic/gin"

func modeFromEnv(appEnv string) string {
	if appEnv == "production" {
		return gin.ReleaseMode
	}
	return gin.DebugMode
}
