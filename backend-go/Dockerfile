# Gunakan image base untuk Go
FROM golang:1.20 AS builder

# Set working directory di dalam container
WORKDIR /app

# Copy semua file proyek ke dalam container
COPY . .

# Inisialisasi modul Go (jika belum ada go.mod)
RUN go mod init trendbox_backend || true

# Unduh dependensi yang diperlukan
RUN go mod tidy

# Build aplikasi tanpa CGO agar kompatibel dengan Alpine
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o app

# Gunakan image lebih ringan untuk runtime
FROM alpine:latest
WORKDIR /root/
COPY --from=builder /app/app .

# Pastikan binary bisa dieksekusi
RUN chmod +x /root/app

# Jalankan aplikasi
CMD ["./app"]