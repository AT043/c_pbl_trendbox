package main

import (
        "database/sql"
        "fmt"
        "log"
        "net/http"
        "os"
        "path/filepath"
        "time"

        "github.com/gin-gonic/gin"
        _ "github.com/lib/pq"
)

const uploadDir = "captured_images"

var db *sql.DB

func main() {
        // Koneksi ke PostgreSQL
        var err error
        db, err = sql.Open("postgres", "postgres://admine_tb:pemerintahajg1113@192.168.10.40:5432/tb_db?sslmode=disable")
        if err != nil {
                log.Fatalf("Gagal koneksi ke database: %v", err)
        }

        // Pastikan folder untuk menyimpan gambar ada
        if err := os.MkdirAll(uploadDir, os.ModePerm); err != nil {
                log.Fatalf("Gagal membuat direktori: %v", err)
        }

        r := gin.Default()
        r.POST("/upload", uploadImage) // Endpoint untuk mengunggah gambar
        r.POST("/insert", insertData) // Endpoint untuk memasukkan data ke database
        r.GET("/results", getMLResults) // Endpoint untuk menampilkan data hasil analisis
        r.GET("/getimages", listImages) // Endpoint untuk mendapatkan daftar gambar
        r.GET("/getimages/:filename", getImage) // Endpoint untuk mengambil gambar tertentu

        // Jalankan server di port 8081
        r.Run(":8081")
}

// uploadImage menangani unggahan gambar dari client dan menyimpannya ke database
func uploadImage(c *gin.Context) {
        file, err := c.FormFile("image")
        if err != nil {
                c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": "No image uploaded"})
                return
        }

        // Buat nama file dengan timestamp
        timestamp := time.Now().Format("20060102_150405")
        filename := fmt.Sprintf("capture_%s.jpg", timestamp)
        filepath := filepath.Join(uploadDir, filename)

        // Simpan file ke storage cloud instance
        if err := c.SaveUploadedFile(file, filepath); err != nil {
                c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": "Failed to save image"})
                return
        }

        c.JSON(http.StatusOK, gin.H{"status": "success", "filename": filename})
}

// insertData menangani penyimpanan data analisis ke database
func insertData(c *gin.Context) {
        var input struct {
                Image           string `json:"image"`
                PeopleCount     int    `json:"people_count"`
                DominantEmotion string `json:"dominant_emotion"`
        }

        if err := c.ShouldBindJSON(&input); err != nil {
                c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": "Invalid input"})
                return
        }

        // Simpan metadata gambar ke database
        query := `
                INSERT INTO ml_results (image_name, people_count, dominant_emotion)
                VALUES ($1, $2, $3)
                ON CONFLICT (image_name) DO NOTHING;
        `
        _, err := db.Exec(query, input.Image, input.PeopleCount, input.DominantEmotion)
        if err != nil {
                c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": "Failed to save data to database"})
                return
        }

        c.JSON(http.StatusOK, gin.H{"status": "success", "message": "Data inserted successfully"})
}


// getMLResults mengambil semua data dari tabel ml_results
func getMLResults(c *gin.Context) {
        rows, err := db.Query("SELECT id, image_name, people_count, dominant_emotion, created_at FROM ml_results ORDER BY created_at DESC")
        if err != nil {
                c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": "Failed to query database"})
                return
        }
        defer rows.Close()

        var results []map[string]interface{}

        for rows.Next() {
                var (
                        id              int
                        imageName       string
                        peopleCount     int
                        dominantEmotion string
                        createdAt       time.Time
                )

                if err := rows.Scan(&id, &imageName, &peopleCount, &dominantEmotion, &createdAt); err != nil {
                        c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": "Failed to scan row"})
                        return
                }

                results = append(results, gin.H{
                        "id":               id,
                        "image_name":       imageName,
                        "people_count":     peopleCount,
                        "dominant_emotion": dominantEmotion,
                        "created_at":       createdAt.Format("2006-01-02 15:04:05"),
                })
        }

        c.JSON(http.StatusOK, gin.H{"status": "success", "results": results})
}


// listImages mengembalikan daftar gambar dalam folder captured_images
func listImages(c *gin.Context) {
        files, err := os.ReadDir(uploadDir)
        if err != nil {
                c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": "Failed to list images"})
                return
        }

        var imageList []string
        for _, file := range files {
                if !file.IsDir() {
                        imageList = append(imageList, file.Name())
                }
        }

        c.JSON(http.StatusOK, gin.H{"images": imageList})
}

// getImage mengembalikan gambar tertentu berdasarkan nama file
func getImage(c *gin.Context) {
        filename := c.Param("filename")
        filePath := filepath.Join(uploadDir, filename)

        // Cek apakah file ada
        if _, err := os.Stat(filePath); os.IsNotExist(err) {
                c.JSON(http.StatusNotFound, gin.H{"status": "error", "message": "Image not found"})
                return
        }

        // Kirim gambar sebagai response
        c.File(filePath)
}
