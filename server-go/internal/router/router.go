package router

import (
	"linte/server-go/internal/config"
	"linte/server-go/internal/handler"
	"linte/server-go/internal/middleware"
	"linte/server-go/internal/pkg/jwtx"
	"linte/server-go/internal/pkg/mailer"
	"linte/server-go/internal/pkg/matcher"
	"linte/server-go/internal/repository"
	"linte/server-go/internal/service"
	"time"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
)

func New(cfg config.Config, db *gorm.DB) (*gin.Engine, error) {
	gin.SetMode(modeFromEnv(cfg.AppEnv))

	engine := gin.Default()
	engine.Use(cors(cfg.AllowOrigins))

	userRepo := repository.NewUserRepository(db)
	codeRepo := repository.NewVerificationCodeRepository(db)
	scheduleRepo := repository.NewScheduleRepository(db)

	jwtManager := jwtx.New(cfg.JWTSecret, cfg.JWTTTL())
	mailerClient := mailer.New(cfg.SMTPHost, cfg.SMTPPort, cfg.SMTPUsername, cfg.SMTPPassword, cfg.SMTPFrom)
	localMatcher := matcher.New(cfg.MatchHighThreshold, cfg.MatchLowThreshold, cfg.MatchFallbackTopN)
	matchEngine := matcher.NewHTTPClient(cfg.MatcherServiceURL, localMatcher)

	authService := service.NewAuthService(userRepo, codeRepo, mailerClient, jwtManager, cfg.CodeTTL(), time.Duration(cfg.CodeSendCooldownSec)*time.Second, cfg.ExposeDebugCode)
	scheduleService := service.NewScheduleService(scheduleRepo)
	matchService := service.NewMatchService(userRepo, scheduleRepo, matchEngine, cfg.NearbyActiveMinutes, cfg.MaxNearbyMatchResults)

	authHandler := handler.NewAuthHandler(authService)
	scheduleHandler := handler.NewScheduleHandler(scheduleService)
	matchHandler := handler.NewMatchHandler(matchService)

	engine.GET("/health", handler.Health)

	api := engine.Group("/api")
	{
		auth := api.Group("/auth")
		{
			auth.POST("/send-code", authHandler.SendCode)
			auth.POST("/register", authHandler.Register)
			auth.POST("/login", authHandler.Login)
			auth.POST("/reset-password", authHandler.ResetPassword)
		}

		protected := api.Group("/")
		protected.Use(middleware.Auth(jwtManager))
		{
			protected.POST("/schedule", scheduleHandler.Create)
			protected.GET("/schedule", scheduleHandler.List)
			protected.PUT("/schedule/:schedule_id", scheduleHandler.Update)
			protected.DELETE("/schedule/:schedule_id", scheduleHandler.Delete)
			protected.POST("/match", matchHandler.RunMatch)
			protected.POST("/user/update-location", matchHandler.UpdateLocation)
			protected.POST("/match/find-nearby-comprehensive", matchHandler.FindNearbyComprehensive)
		}
	}

	return engine, nil
}
