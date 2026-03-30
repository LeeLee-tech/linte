package password

import "golang.org/x/crypto/bcrypt"

const bcryptLimit = 72

func Hash(raw string) (string, error) {
	bytes := []byte(raw)
	if len(bytes) > bcryptLimit {
		bytes = bytes[:bcryptLimit]
	}

	hashed, err := bcrypt.GenerateFromPassword(bytes, bcrypt.DefaultCost)
	if err != nil {
		return "", err
	}
	return string(hashed), nil
}

func Verify(raw, hashed string) bool {
	bytes := []byte(raw)
	if len(bytes) > bcryptLimit {
		bytes = bytes[:bcryptLimit]
	}
	return bcrypt.CompareHashAndPassword([]byte(hashed), bytes) == nil
}
