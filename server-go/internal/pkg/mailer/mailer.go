package mailer

import (
	"crypto/tls"
	"fmt"
	"log"
	"net/smtp"
)

type Mailer interface {
	SendVerificationCode(toEmail, code string) error
	IsConfigured() bool
}

type SMTPMailer struct {
	host     string
	port     int
	username string
	password string
	from     string
}

type DummyMailer struct{}

func New(host string, port int, username, password, from string) Mailer {
	if username == "" || password == "" || from == "" {
		log.Printf("smtp not configured, using dummy mailer")
		return DummyMailer{}
	}

	return &SMTPMailer{
		host:     host,
		port:     port,
		username: username,
		password: password,
		from:     from,
	}
}

func (m *SMTPMailer) SendVerificationCode(toEmail, code string) error {
	subject := "Subject: [Linte] Verification Code\r\n"
	headers := "MIME-Version: 1.0\r\nContent-Type: text/html; charset=\"UTF-8\"\r\n"
	body := fmt.Sprintf(`
<html>
<body>
  <h3>Your verification code is:</h3>
  <h1 style="color:#007bff;font-size:40px;letter-spacing:5px;">%s</h1>
  <p>The code expires in 5 minutes.</p>
</body>
</html>`, code)
	message := []byte(subject + headers + "\r\n" + body)

	addr := fmt.Sprintf("%s:%d", m.host, m.port)
	conn, err := tls.Dial("tcp", addr, &tls.Config{ServerName: m.host})
	if err != nil {
		return err
	}
	defer conn.Close()

	client, err := smtp.NewClient(conn, m.host)
	if err != nil {
		return err
	}
	defer client.Quit()

	auth := smtp.PlainAuth("", m.username, m.password, m.host)
	if err := client.Auth(auth); err != nil {
		return err
	}
	if err := client.Mail(m.from); err != nil {
		return err
	}
	if err := client.Rcpt(toEmail); err != nil {
		return err
	}

	writer, err := client.Data()
	if err != nil {
		return err
	}
	if _, err := writer.Write(message); err != nil {
		return err
	}
	return writer.Close()
}

func (*SMTPMailer) IsConfigured() bool {
	return true
}

func (DummyMailer) SendVerificationCode(toEmail, code string) error {
	log.Printf("[dummy_mailer] verification code for %s: %s", toEmail, code)
	return nil
}

func (DummyMailer) IsConfigured() bool {
	return false
}
