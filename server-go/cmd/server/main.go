package main

import (
	"context"
	"log"
	"os"
	"os/signal"
	"syscall"

	"linte/server-go/internal/config"
	"linte/server-go/internal/database"
	"linte/server-go/internal/pkg/matcher"
	"linte/server-go/internal/router"
)

func main() {
	cfg := config.Load()

	db, err := database.New(cfg.DatabaseURL)
	if err != nil {
		log.Fatalf("failed to connect database: %v", err)
	}

	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer cancel()

	if cfg.AutoStartMatcher {
		matcher.StartLocalService(ctx, matcher.LaunchConfig{
			ServiceURL: cfg.MatcherServiceURL,
			ModelPath:  cfg.MatcherModelPath,
		})
	}

	engine, err := router.New(cfg, db)
	if err != nil {
		log.Fatalf("failed to build router: %v", err)
	}

	log.Printf("server listening on %s", cfg.ListenAddr())
	if err := engine.Run(cfg.ListenAddr()); err != nil {
		log.Fatalf("server stopped: %v", err)
	}
}
