package config

import (
	"os"
	"strconv"
	"strings"
	"time"
)

type Config struct {
	AppEnv                string
	Host                  string
	Port                  string
	DatabaseURL           string
	JWTSecret             string
	JWTExpireMinutes      int
	CodeExpireMinutes     int
	CodeSendCooldownSec   int
	NearbyActiveMinutes   int
	SMTPHost              string
	SMTPPort              int
	SMTPUsername          string
	SMTPPassword          string
	SMTPFrom              string
	ExposeDebugCode       bool
	AllowOrigins          []string
	MatcherServiceURL     string
	AutoStartMatcher      bool
	MatcherModelPath      string
	MatchHighThreshold    float64
	MatchLowThreshold     float64
	MatchFallbackTopN     int
	MaxNearbyMatchResults int
}

func Load() Config {
	return Config{
		AppEnv:                getEnv("APP_ENV", "development"),
		Host:                  getEnv("HOST", "0.0.0.0"),
		Port:                  getEnv("PORT", "8000"),
		DatabaseURL:           getEnv("DATABASE_URL", "schedule.db"),
		JWTSecret:             getEnv("JWT_SECRET", "your_super_secret_key_change_this"),
		JWTExpireMinutes:      getEnvAsInt("JWT_EXPIRE_MINUTES", 30),
		CodeExpireMinutes:     getEnvAsInt("CODE_EXPIRE_MINUTES", 5),
		CodeSendCooldownSec:   getEnvAsInt("CODE_SEND_COOLDOWN_SECONDS", 60),
		NearbyActiveMinutes:   getEnvAsInt("NEARBY_ACTIVE_MINUTES", 10),
		SMTPHost:              getEnv("SMTP_HOST", "smtp.qq.com"),
		SMTPPort:              getEnvAsInt("SMTP_PORT", 465),
		SMTPUsername:          firstNonEmpty(os.Getenv("QQ_EMAIL"), os.Getenv("SMTP_USERNAME")),
		SMTPPassword:          firstNonEmpty(os.Getenv("QQ_AUTH_CODE"), os.Getenv("SMTP_PASSWORD")),
		SMTPFrom:              firstNonEmpty(os.Getenv("SMTP_FROM"), os.Getenv("QQ_EMAIL"), os.Getenv("SMTP_USERNAME")),
		ExposeDebugCode:       getEnvAsBool("EXPOSE_DEBUG_CODE", getEnv("APP_ENV", "development") != "production"),
		AllowOrigins:          splitCSV(getEnv("ALLOW_ORIGINS", "*")),
		MatcherServiceURL:     getEnv("MATCHER_SERVICE_URL", "http://127.0.0.1:8010"),
		AutoStartMatcher:      getEnvAsBool("MATCHER_AUTOSTART", true),
		MatcherModelPath:      getEnv("MATCHER_MODEL_PATH", `D:\models\bge-large-zh-v1.5`),
		MatchHighThreshold:    getEnvAsFloat("MATCH_HIGH_THRESHOLD", 0.77),
		MatchLowThreshold:     getEnvAsFloat("MATCH_LOW_THRESHOLD", 0.45),
		MatchFallbackTopN:     getEnvAsInt("MATCH_FALLBACK_TOP_N", 2),
		MaxNearbyMatchResults: getEnvAsInt("MAX_NEARBY_MATCH_RESULTS", 20),
	}
}

func (c Config) ListenAddr() string {
	return c.Host + ":" + c.Port
}

func (c Config) JWTTTL() time.Duration {
	return time.Duration(c.JWTExpireMinutes) * time.Minute
}

func (c Config) CodeTTL() time.Duration {
	return time.Duration(c.CodeExpireMinutes) * time.Minute
}

func getEnv(key, fallback string) string {
	value := strings.TrimSpace(os.Getenv(key))
	if value == "" {
		return fallback
	}
	return value
}

func getEnvAsInt(key string, fallback int) int {
	raw := strings.TrimSpace(os.Getenv(key))
	if raw == "" {
		return fallback
	}
	value, err := strconv.Atoi(raw)
	if err != nil {
		return fallback
	}
	return value
}

func getEnvAsFloat(key string, fallback float64) float64 {
	raw := strings.TrimSpace(os.Getenv(key))
	if raw == "" {
		return fallback
	}
	value, err := strconv.ParseFloat(raw, 64)
	if err != nil {
		return fallback
	}
	return value
}

func getEnvAsBool(key string, fallback bool) bool {
	raw := strings.TrimSpace(os.Getenv(key))
	if raw == "" {
		return fallback
	}
	switch strings.ToLower(raw) {
	case "1", "true", "yes", "y", "on":
		return true
	case "0", "false", "no", "n", "off":
		return false
	default:
		return fallback
	}
}

func splitCSV(value string) []string {
	parts := strings.Split(value, ",")
	items := make([]string, 0, len(parts))
	for _, part := range parts {
		trimmed := strings.TrimSpace(part)
		if trimmed != "" {
			items = append(items, trimmed)
		}
	}
	if len(items) == 0 {
		return []string{"*"}
	}
	return items
}

func firstNonEmpty(values ...string) string {
	for _, value := range values {
		if strings.TrimSpace(value) != "" {
			return value
		}
	}
	return ""
}
