package main

import (
	"fmt"
	"log"
	"sync/atomic"
	"time"

	"github.com/gorilla/websocket"
)

const (
	streamURL      = "wss://stream.binance.com:9443/ws/btcusdt@ticker"
	numMessages    = 100 // Number of messages to send
	sleepInterval  = 100 * time.Millisecond // 100ms between sends
)

var (
	totalLatency int64
	totalMessages int64
)

func main() {
	fmt.Println("Starting WebSocket benchmark...")

	// Connect to Binance WebSocket
	conn, _, err := websocket.DefaultDialer.Dial(streamURL, nil)
	if err != nil {
		log.Fatal("Connection error:", err)
	}
	defer conn.Close()

	// Run the benchmark
	for i := 0; i < numMessages; i++ {
		go sendAndMeasure(conn)
		time.Sleep(sleepInterval)
	}

	// Wait for all messages to complete
	time.Sleep(5 * time.Second)

	// Compute average latency
	if totalMessages > 0 {
		avgLatency := time.Duration(totalLatency / totalMessages)
		fmt.Printf("\n--- Benchmark Results ---\n")
		fmt.Printf("Messages Sent: %d\n", totalMessages)
		fmt.Printf("Average Round-trip Latency: %v\n", avgLatency)
	} else {
		fmt.Println("No messages were processed.")
	}
}

func sendAndMeasure(conn *websocket.Conn) {
	// Timestamp before send
	startTime := time.Now()

	// Send a ping frame
	if err := conn.WriteMessage(websocket.PingMessage, []byte("ping")); err != nil {
		log.Println("Write error:", err)
		return
	}

	// Read pong response
	_, _, err := conn.ReadMessage()
	if err != nil {
		log.Println("Read error:", err)
		return
	}

	// Timestamp after receive
	latency := time.Since(startTime)

	// Atomically update counters
	atomic.AddInt64(&totalLatency, latency.Nanoseconds())
	atomic.AddInt64(&totalMessages, 1)

	fmt.Printf("Message #%d: Latency = %v\n", totalMessages, latency)
}
