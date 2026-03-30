package matcher

import (
	"math"
	"regexp"
	"sort"
	"strings"
	"time"
	"unicode/utf8"
)

type Input struct {
	ID        string
	TimeRange string
	Content   string
}

type Matcher interface {
	Match(profile Input, candidates []Input) []Result
}

type Result struct {
	ID      string  `json:"id"`
	Time    string  `json:"time"`
	Content string  `json:"content"`
	Score   float64 `json:"score"`
	Level   string  `json:"level"`
}

type Engine struct {
	highThreshold float64
	lowThreshold  float64
	fallbackTopN  int
}

func New(highThreshold, lowThreshold float64, fallbackTopN int) *Engine {
	return &Engine{
		highThreshold: highThreshold,
		lowThreshold:  lowThreshold,
		fallbackTopN:  fallbackTopN,
	}
}

func (e *Engine) Match(profile Input, candidates []Input) []Result {
	myStart, myEnd, ok := parseTimeRange(profile.TimeRange)
	if !ok {
		return nil
	}

	high := make([]Result, 0)
	fallback := make([]Result, 0)

	for _, candidate := range candidates {
		candidateStart, candidateEnd, ok := parseTimeRange(candidate.TimeRange)
		if !ok || !overlap(myStart, myEnd, candidateStart, candidateEnd) {
			continue
		}

		score := semanticScore(profile.Content, candidate.Content)
		result := Result{
			ID:      candidate.ID,
			Time:    candidate.TimeRange,
			Content: candidate.Content,
			Score:   round(score, 4),
		}

		switch {
		case score >= e.highThreshold:
			result.Level = "high"
			high = append(high, result)
		case score >= e.lowThreshold:
			result.Level = "medium"
			fallback = append(fallback, result)
		}
	}

	sort.Slice(high, func(i, j int) bool { return high[i].Score > high[j].Score })
	sort.Slice(fallback, func(i, j int) bool { return fallback[i].Score > fallback[j].Score })

	if len(high) > 0 {
		return high
	}
	if len(fallback) > e.fallbackTopN {
		return fallback[:e.fallbackTopN]
	}
	return fallback
}

func semanticScore(left, right string) float64 {
	leftTokens := tokenize(left)
	rightTokens := tokenize(right)
	if len(leftTokens) == 0 || len(rightTokens) == 0 {
		return 0
	}

	leftSet := make(map[string]struct{}, len(leftTokens))
	rightSet := make(map[string]struct{}, len(rightTokens))
	for _, token := range leftTokens {
		leftSet[token] = struct{}{}
	}
	for _, token := range rightTokens {
		rightSet[token] = struct{}{}
	}

	intersection := 0
	for token := range leftSet {
		if _, ok := rightSet[token]; ok {
			intersection++
		}
	}

	union := len(leftSet) + len(rightSet) - intersection
	if union == 0 {
		return 0
	}

	jaccard := float64(intersection) / float64(union)
	charScore := charOverlap(left, right)
	return 0.7*jaccard + 0.3*charScore
}

func tokenize(text string) []string {
	lower := strings.ToLower(strings.TrimSpace(text))
	wordPattern := regexp.MustCompile(`[a-z0-9]+`)
	words := wordPattern.FindAllString(lower, -1)
	tokens := make([]string, 0, len(words))
	tokens = append(tokens, words...)

	for _, r := range []rune(lower) {
		if utf8.RuneLen(r) > 0 && !strings.ContainsRune(" \t\r\n,.;:!?()[]{}<>/\\'\"-_", r) && r > 127 {
			tokens = append(tokens, string(r))
		}
	}
	return tokens
}

func charOverlap(left, right string) float64 {
	leftRunes := []rune(strings.TrimSpace(left))
	rightRunes := []rune(strings.TrimSpace(right))
	if len(leftRunes) == 0 || len(rightRunes) == 0 {
		return 0
	}

	leftCount := map[rune]int{}
	rightCount := map[rune]int{}
	for _, r := range leftRunes {
		leftCount[r]++
	}
	for _, r := range rightRunes {
		rightCount[r]++
	}

	common := 0
	for r, count := range leftCount {
		if other, ok := rightCount[r]; ok {
			common += min(count, other)
		}
	}

	return float64(common*2) / float64(len(leftRunes)+len(rightRunes))
}

func parseTimeRange(timeRange string) (time.Time, time.Time, bool) {
	parts := strings.SplitN(strings.TrimSpace(timeRange), "-", 2)
	if len(parts) != 2 {
		return time.Time{}, time.Time{}, false
	}

	today := time.Now()
	startClock, err := time.Parse("15:04", strings.TrimSpace(parts[0]))
	if err != nil {
		return time.Time{}, time.Time{}, false
	}
	endClock, err := time.Parse("15:04", strings.TrimSpace(parts[1]))
	if err != nil {
		return time.Time{}, time.Time{}, false
	}

	start := time.Date(today.Year(), today.Month(), today.Day(), startClock.Hour(), startClock.Minute(), 0, 0, time.Local)
	end := time.Date(today.Year(), today.Month(), today.Day(), endClock.Hour(), endClock.Minute(), 0, 0, time.Local)
	if end.Before(start) {
		end = end.Add(24 * time.Hour)
	}
	return start, end, true
}

func overlap(startA, endA, startB, endB time.Time) bool {
	return startA.Before(endB) && endA.After(startB)
}

func round(value float64, precision int) float64 {
	pow := math.Pow(10, float64(precision))
	return math.Round(value*pow) / pow
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
