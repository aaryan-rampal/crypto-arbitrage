package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"github.com/gorilla/websocket"
)

const streamURL = "wss://stream.binance.com:9443/ws/btcusdt@bookTicker/ethusdt@bookTicker/ethbtc@bookTicker"

type BookTicker struct {
	Stream string `json:"stream"`
	Data   struct {
		Symbol string `json:"s"`
		Bid    string `json:"b"`
		Ask    string `json:"a"`
	} `json:"data"`
}

var prices = struct {
	sync.RWMutex
	data map[string]map[string]float64
}{
	data: make(map[string]map[string]float64),
}

func main() {
	// context.withCancel makes sure all go-routines 
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Capture exit signals
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

	// Start WebSocket Listener
	go listenWebSocket(ctx)

	// Stop on signal
	select {
	case <-sigCh:
		fmt.Println("\nShutting down...")
		cancel()
		time.Sleep(2 * time.Second) // grace period
	}
}

func listenWebSocket(ctx context.Context) {
	headers := http.Header{}
	headers.Add("User-Agent", "go-arbitrage-bot/1.0")

	conn, resp, err := websocket.DefaultDialer.Dial(streamURL, headers)
	if err != nil {
		if resp != nil {
			fmt.Println("HTTP Status Code:", resp.StatusCode)
			fmt.Println("HTTP Response:", resp)
			log.Fatal("WebSocket connection error:", err)
		} else {
			fmt.Println("No HTTP Response received")
		}
		log.Fatal("WebSocket connection error:", err)
	}
	defer conn.Close()

	fmt.Println("Connected to Binance WebSocket...")

	for {
		select {
		case <-ctx.Done():
			fmt.Println("Closing WebSocket connection...")
			return
		default:
			_, message, err := conn.ReadMessage()
			if err != nil {
				log.Println("Read error:", err)
				continue
			}

			var ticker BookTicker
			if err := json.Unmarshal(message, &ticker); err != nil {
				log.Println("JSON Unmarshal error:", err)
				continue
			}

			// Update price map
			prices.Lock()
			if prices.data[ticker.Data.Symbol] == nil {
				prices.data[ticker.Data.Symbol] = make(map[string]float64)
			}

			// Check if Ask is non-empty and valid before updating
			if ticker.Data.Ask != "" {
				askPrice := parseFloat(ticker.Data.Ask)
				prices.data[ticker.Data.Symbol]["ask"] = askPrice
			}

			// Check if Bid is non-empty and valid before updating
			if ticker.Data.Bid != "" {
				bidPrice := parseFloat(ticker.Data.Bid)
				prices.data[ticker.Data.Symbol]["bid"] = bidPrice
			}

			prices.Unlock()

			// Compute arbitrage
			computeArbitrage()
		}
	}
}

func parseFloat(value string) float64 {
	val, err := json.Number(value).Float64()
	if err != nil {
		log.Println("Conversion error:", err)
	}
	return val
}

func computeArbitrage() {
	prices.RLock()
	defer prices.RUnlock()

	btcAsk := prices.data["BTCUSDT"]["ask"]
	ethAsk := prices.data["ETHBTC"]["ask"]
	ethBid := prices.data["ETHUSDT"]["bid"]

	if btcAsk > 0 && ethAsk > 0 && ethBid > 0 {
		ratio := (1 / btcAsk) * (1 / ethAsk) * ethBid
		fmt.Printf("[%s] Arbitrage ratio: %.6f\n", time.Now().Format("15:04:05"), ratio)
	}
}
