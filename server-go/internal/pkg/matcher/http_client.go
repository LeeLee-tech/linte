package matcher

import (
	"bytes"
	"encoding/json"
	"log"
	"net/http"
	"strings"
	"time"
)

type HTTPClient struct {
	baseURL  string
	client   *http.Client
	fallback Matcher
}

type httpMatchRequest struct {
	MyProfile  Input   `json:"my_profile"`
	Candidates []Input `json:"candidates"`
}

type httpMatchResponse struct {
	Matches []Result `json:"matches"`
}

func NewHTTPClient(baseURL string, fallback Matcher) Matcher {
	trimmed := strings.TrimRight(strings.TrimSpace(baseURL), "/")
	if trimmed == "" {
		return fallback
	}

	return &HTTPClient{
		baseURL: trimmed,
		client: &http.Client{
			Timeout: 8 * time.Second,
		},
		fallback: fallback,
	}
}

func (h *HTTPClient) Match(profile Input, candidates []Input) []Result {
	payload, err := json.Marshal(httpMatchRequest{
		MyProfile:  profile,
		Candidates: candidates,
	})
	if err != nil {
		return h.fallback.Match(profile, candidates)
	}

	resp, err := h.client.Post(h.baseURL+"/match", "application/json", bytes.NewReader(payload))
	if err != nil {
		log.Printf("matcher service unavailable, using fallback: %v", err)
		return h.fallback.Match(profile, candidates)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 300 {
		log.Printf("matcher service returned status %d, using fallback", resp.StatusCode)
		return h.fallback.Match(profile, candidates)
	}

	var result httpMatchResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		log.Printf("matcher response decode failed, using fallback: %v", err)
		return h.fallback.Match(profile, candidates)
	}
	return result.Matches
}
