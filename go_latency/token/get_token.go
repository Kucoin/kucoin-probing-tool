package token

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
)

var Result struct {
	Code string `json:"code"`
	Data struct {
		Token           string `json:"token"`
		InstanceServers []struct {
			Endpoint     string `json:"endpoint"`
			Encrypt      bool   `json:"encrypt"`
			Protocol     string `json:"protocol"`
			PingInterval int    `json:"pingInterval"`
			PingTimeout  int    `json:"pingTimeout"`
		} `json:"instanceServers"`
	} `json:"data"`
}

func GetToken() (string, string, error) {
	url := "https://api.kucoin.com/api/v1/bullet-public"
	req, err := http.NewRequest("POST", url, nil)
	if err != nil {
		return "", "", err
	}

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return "", "", err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", "", err
	}

	if err := json.Unmarshal(body, &Result); err != nil {
		return "", "", err
	}

	if Result.Code != "200000" {
		return "", "", fmt.Errorf("API error with code: %s", Result.Code)
	}

	if len(Result.Data.InstanceServers) == 0 {
		return "", "", fmt.Errorf("no servers returned by API")
	}

	return Result.Data.InstanceServers[0].Endpoint + "?token=" + Result.Data.Token, Result.Data.Token, nil
}
