# AI-Powered DevOps Testing Platform

Modern AI destekli DevOps testing platformu için FastAPI backend projesi. OpenAI GPT-3.5-turbo entegrasyonu ile doğal dil komutlarını anlayıp otomatik test stratejileri oluşturur.

## 🚀 Özellikler

- **🤖 AI-Powered Testing**: OpenAI GPT-3.5-turbo ile doğal dil komut işleme
- **🧠 AI Strategy Execution**: AI stratejisini Selenium koduna çevirme
- **🌐 Selenium Web Automation**: Kapsamlı web otomasyonu ve element interaction
- **📱 Social Media Testing**: Instagram, Facebook, Twitter vb. platform testleri
- **📊 Structured Test Results**: Detaylı test adımları ve başarı oranları
- **📸 Screenshot Capture**: Otomatik ekran görüntüsü alma
- **🎯 High Quality Mode**: Comprehensive testing with full screenshots and detailed reporting
- **🚀 Performance Optimized**: Headless browser support, async operations, detailed metrics
- **⚡ FastAPI Async Backend**: Yüksek performanslı async web framework
- **🔧 Modern Architecture**: Clean architecture ve dependency injection
- **🐳 Docker Support**: Containerized deployment
- **📈 Performance Monitoring**: Test süreleri ve performans metrikleri
- **🔄 Retry Mechanism**: OpenAI API için akıllı retry sistemi
- **📝 Comprehensive Logging**: Detaylı loglama ve hata takibi

## 🎯 AI Özellikleri

### Doğal Dil Komut İşleme
```bash
# Örnek komutlar
"Instagram'ı test et"
"Facebook login sayfasını kontrol et"
"Twitter performans testi yap"
"LinkedIn güvenlik testi"
```

### Desteklenen Platformlar
- **Instagram**: Login, feed, profile, navigation testleri
- **Facebook**: UI ve functional testler
- **Twitter**: Performance ve accessibility testleri
- **LinkedIn**: Security ve professional features
- **YouTube**: Video ve channel testleri
- **TikTok**: Short video ve engagement testleri

### Test Türleri
- **UI Testing**: Görsel arayüz testleri
- **Functional Testing**: İşlevsel testler
- **Performance Testing**: Performans testleri
- **Security Testing**: Güvenlik testleri
- **Accessibility Testing**: Erişilebilirlik testleri
- **E2E Testing**: End-to-end testler

## 📁 Proje Yapısı

```
ai-devops-platform/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI uygulama girişi
│   ├── core/                   # Temel konfigürasyon
│   │   ├── __init__.py
│   │   ├── config.py           # Uygulama ayarları
│   │   ├── database.py         # Database bağlantısı
│   │   ├── ai_engine.py        # AI Engine - OpenAI entegrasyonu
│   │   └── security.py         # Güvenlik ayarları
│   ├── integrations/           # Harici servis entegrasyonları
│   │   ├── __init__.py
│   │   └── openai_client.py    # OpenAI API client
│   ├── modules/                # Ana modüller
│   │   ├── __init__.py
│   │   └── web_automation.py   # Selenium web otomasyonu
│   ├── api/                    # API endpoints
│   ├── models/                 # Database modelleri
│   ├── schemas/                # Pydantic şemaları
│   ├── services/               # İş mantığı servisleri
│   ├── tasks/                  # Celery görevleri
│   └── utils/                  # Yardımcı fonksiyonlar
├── test_results/               # Test sonuçları ve raporlar
├── tests/                      # Test dosyaları
├── requirements.txt            # Python bağımlılıkları
├── test_ai_platform.py         # AI platform test scripti
├── Dockerfile                  # Docker image
├── docker-compose.yml          # Docker Compose
├── env.example                 # Environment örneği
└── README.md
```

## 🛠️ Kurulum

### Gereksinimler

- Python 3.11+
- Docker & Docker Compose
- OpenAI API Key
- Chrome/Chromium browser

### 1. Repository'yi klonlayın

```bash
git clone <repository-url>
cd ai-devops-platform
```

### 2. Environment dosyasını oluşturun

```bash
cp env.example .env
```

### 3. OpenAI API Key'i ayarlayın

```bash
# .env dosyasında
OPENAI_API_KEY=your-openai-api-key-here
```

### 4. Docker ile çalıştırın

```bash
docker-compose up -d
```

### 5. Uygulamaya erişin

- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🧪 Kullanım Örnekleri

### 1. AI Komut İşleme (Selenium Automation)

```bash
# Basit Instagram testi
curl -X POST "http://localhost:8000/api/v1/ai/command" \
  -H "Content-Type: application/json" \
  -d '{"command": "Instagram'\''ı test et"}'

# Gelişmiş test komutu
curl -X POST "http://localhost:8000/api/v1/ai/command" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "Instagram'\''da login formunu ve navigation elementlerini test et",
    "platform": "instagram",
    "test_type": "functional",
    "priority": "high",
    "fast_mode": false,
    "context": {
      "browser": "chrome",
      "headless": true,
      "timeout": 30
    }
  }'

# Headless Mode test komutu (GUI olmadan)
curl -X POST "http://localhost:8000/api/v1/ai/command" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "Instagram ana sayfasını headless test et",
    "platform": "instagram",
    "test_type": "ui",
    "priority": "medium",
    "headless": true,
    "context": {
      "browser": "chrome",
      "headless": true,
      "timeout": 30
    }
  }'

# Facebook testi
curl -X POST "http://localhost:8000/api/v1/ai/command" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "Facebook ana sayfasını test et",
    "platform": "facebook",
    "test_type": "ui"
  }'
```

### 2. Platform Özel Testi (AI Strategy)

```bash
# Instagram hızlı testi - AI stratejisi ile
curl -X GET "http://localhost:8000/api/v1/ai/test/instagram"
```

### 3. Manuel Automation Stratejisi

```bash
# Manuel olarak automation stratejisi çalıştır
curl -X POST "http://localhost:8000/api/v1/automation/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "instagram",
    "test_type": "e2e",
    "steps": [
      "1. Instagram ana sayfasını aç",
      "2. Logo kontrolü yap",
      "3. Login formunu kontrol et",
      "4. Navigation elementlerini test et",
      "5. Screenshot al"
    ],
    "priority": "high",
    "estimated_time": 120,
    "test_scenarios": [
      {
        "name": "Login Form Test",
        "description": "Login form elementlerini kontrol et"
      },
      {
        "name": "Navigation Test", 
        "description": "Navigation elementlerini test et"
      }
    ]
  }'
```

### 4. Automation Sistem Durumu

```bash
# Automation sistem durumunu kontrol et
curl -X GET "http://localhost:8000/api/v1/automation/status"
```

### 5. Test Raporları

```bash
# Tüm raporları listele
curl -X GET "http://localhost:8000/api/v1/reports"

# Belirli raporu getir
curl -X GET "http://localhost:8000/api/v1/reports/instagram_ai_test_report.json"
```

### 4. Python Test Scripti

```bash
# Test scriptini çalıştır
python test_ai_platform.py
```

## 📚 API Endpoints

### AI Endpoints
- `POST /api/v1/ai/command` - Doğal dil komut işleme + Selenium automation
- `GET /api/v1/ai/config` - AI konfigürasyon bilgileri
- `GET /api/v1/ai/test/{platform}` - Platform özel testi (AI strategy)

### Automation Endpoints
- `POST /api/v1/automation/execute` - Manuel automation stratejisi çalıştırma
- `GET /api/v1/automation/status` - Automation sistem durumu

### Test Reports
- `GET /api/v1/reports` - Test raporları listesi
- `GET /api/v1/reports/{filename}` - Belirli test raporu

### System
- `GET /health` - Sistem sağlık kontrolü
- `GET /` - Ana sayfa ve özellikler

## 🔧 Geliştirme

### Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate     # Windows
```

### Bağımlılıkları yükleyin

```bash
pip install -r requirements.txt
```

### Uygulamayı çalıştırın

```bash
python -m uvicorn app.main:app --reload
```

## 🧪 Testler

### AI Platform Testi

```bash
python test_ai_platform.py
```

### Manuel Test

```bash
# 1. Sağlık kontrolü
curl http://localhost:8000/health

# 2. AI komut testi
curl -X POST "http://localhost:8000/api/v1/ai/command" \
  -H "Content-Type: application/json" \
  -d '{"command": "Instagram'\''ı test et"}'

# 3. Test raporları
curl http://localhost:8000/api/v1/reports
```

## 📊 Test Sonuçları

Test sonuçları `test_results/` dizininde saklanır:

- **Screenshots**: Ekran görüntüleri
- **JSON Reports**: Detaylı test raporları
- **Performance Metrics**: Test süreleri ve performans verileri

### Örnek Test Raporu

```json
{
  "command": "Instagram'ı test et",
  "ai_analysis": {
    "parsed_intent": "test_platform",
    "platform": "instagram",
    "test_type": "e2e",
    "confidence": 0.95
  },
  "test_strategy": {
    "steps": ["1. Login test", "2. Navigation test", "3. Feature test"],
    "priority": "high",
    "estimated_time": "10-15 minutes"
  },
  "automation_results": {
    "success": true,
    "test_duration": 12.5,
    "elements_found": 15,
    "screenshots": ["instagram_login_form.png", "instagram_final.png"]
  }
}
```

## 🔐 Güvenlik

- **OpenAI API Key**: Environment variables ile güvenli saklama
- **CORS**: Cross-origin resource sharing konfigürasyonu
- **Input Validation**: Pydantic ile giriş doğrulama
- **Error Handling**: Kapsamlı hata yönetimi

## 🚀 Deployment

### Production

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables

Production ortamında aşağıdaki environment değişkenlerini ayarlayın:

```bash
# OpenAI
OPENAI_API_KEY=your-production-api-key
OPENAI_MODEL=gpt-4
OPENAI_MAX_RETRIES=3

# Web Automation
SELENIUM_HEADLESS=True
CHROME_DRIVER_PATH=/usr/bin/chromedriver

# Performance
MAX_CONCURRENT_TESTS=5
TEST_TIMEOUT=300
```

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit yapın (`git commit -m 'Add amazing feature'`)
4. Push yapın (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 🆘 Destek

Sorunlarınız için:
- GitHub Issues: [Proje Issues](https://github.com/your-repo/issues)
- Email: support@example.com

## 🔮 Gelecek Özellikler

- [ ] Mobile app testing
- [ ] API testing automation
- [ ] Load testing integration
- [ ] CI/CD pipeline integration
- [ ] Multi-language support
- [ ] Advanced AI models (GPT-4, Claude)
- [ ] Real-time test monitoring
- [ ] Test analytics dashboard 