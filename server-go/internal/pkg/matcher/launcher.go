package matcher

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"time"
)

type LaunchConfig struct {
	ServiceURL string
	ModelPath  string
}

func StartLocalService(ctx context.Context, cfg LaunchConfig) {
	workingDir := filepath.Join("..", "matcher-service")
	appPath := filepath.Join(workingDir, "app.py")
	if _, err := os.Stat(appPath); err != nil {
		log.Printf("matcher service not found at %s, skipping autostart", appPath)
		return
	}

	cmd := exec.CommandContext(ctx, "python", "app.py")
	cmd.Dir = workingDir
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Env = append(os.Environ(),
		"MATCHER_HOST=0.0.0.0",
		"MATCHER_PORT=8010",
		"MATCHER_MODEL_PATH="+cfg.ModelPath,
	)

	if err := cmd.Start(); err != nil {
		log.Printf("failed to start matcher service: %v", err)
		return
	}

	go func() {
		<-ctx.Done()
		_ = cmd.Process.Kill()
	}()

	go waitForHealth(cfg.ServiceURL)
}

func waitForHealth(serviceURL string) {
	client := http.Client{Timeout: 2 * time.Second}
	for i := 0; i < 10; i++ {
		resp, err := client.Get(serviceURL + "/health")
		if err == nil && resp.StatusCode < 300 {
			_ = resp.Body.Close()
			log.Printf("matcher service ready at %s", serviceURL)
			return
		}
		if resp != nil {
			_ = resp.Body.Close()
		}
		time.Sleep(800 * time.Millisecond)
	}
	log.Printf("matcher service did not become healthy, continuing with fallback")
}
