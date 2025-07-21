#!/usr/bin/env python3
"""
AI DevOps Platform Başlatma Scripti
Kolay kurulum ve test için
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def check_python_version():
    """Python versiyonunu kontrol et"""
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ gerekli!")
        print(f"   Mevcut versiyon: {sys.version}")
        return False
    print(f"✅ Python versiyonu: {sys.version}")
    return True

def check_dependencies():
    """Gerekli bağımlılıkları kontrol et"""
    print("🔍 Bağımlılıklar kontrol ediliyor...")
    
    required_packages = [
        "fastapi", "uvicorn", "pydantic", "python-dotenv",
        "aiohttp", "openai", "selenium", "webdriver-manager"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} eksik")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 Eksik paketler yükleniyor: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
            print("✅ Bağımlılıklar yüklendi")
        except subprocess.CalledProcessError:
            print("❌ Bağımlılık yükleme hatası!")
            return False
    
    return True

def check_env_file():
    """Environment dosyasını kontrol et"""
    print("🔧 Environment dosyası kontrol ediliyor...")
    
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if not env_file.exists():
        if env_example.exists():
            print("📝 .env dosyası oluşturuluyor...")
            subprocess.run(["cp", "env.example", ".env"])
            print("⚠️  Lütfen .env dosyasında OPENAI_API_KEY'i ayarlayın!")
            return False
        else:
            print("❌ env.example dosyası bulunamadı!")
            return False
    else:
        print("✅ .env dosyası mevcut")
        
        # OpenAI API key kontrolü
        with open(env_file, 'r') as f:
            content = f.read()
            if "your-openai-api-key-here" in content:
                print("⚠️  Lütfen .env dosyasında OPENAI_API_KEY'i ayarlayın!")
                return False
            elif "OPENAI_API_KEY=" in content:
                print("✅ OpenAI API Key ayarlanmış")
                return True
    
    return True

def start_server():
    """FastAPI sunucusunu başlat"""
    print("🚀 FastAPI sunucusu başlatılıyor...")
    
    try:
        # Sunucuyu arka planda başlat
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--reload"
        ])
        
        # Sunucunun başlamasını bekle
        print("⏳ Sunucu başlatılıyor...")
        time.sleep(5)
        
        # Sağlık kontrolü
        try:
            response = requests.get("http://localhost:8000/health", timeout=10)
            if response.status_code == 200:
                print("✅ Sunucu başarıyla başlatıldı!")
                print("🌐 API: http://localhost:8000")
                print("📚 Docs: http://localhost:8000/docs")
                return process
            else:
                print(f"❌ Sunucu yanıt vermiyor: {response.status_code}")
                process.terminate()
                return None
        except requests.exceptions.RequestException:
            print("❌ Sunucu bağlantı hatası!")
            process.terminate()
            return None
            
    except Exception as e:
        print(f"❌ Sunucu başlatma hatası: {e}")
        return None

def run_tests():
    """Test scriptini çalıştır"""
    print("🧪 Test scripti çalıştırılıyor...")
    
    test_script = Path("test_ai_platform.py")
    if test_script.exists():
        try:
            subprocess.run([sys.executable, "test_ai_platform.py"])
        except subprocess.CalledProcessError as e:
            print(f"❌ Test hatası: {e}")
    else:
        print("⚠️  test_ai_platform.py bulunamadı")

def main():
    """Ana fonksiyon"""
    print("🤖 AI DevOps Platform Başlatılıyor...")
    print("=" * 50)
    
    # 1. Python versiyon kontrolü
    if not check_python_version():
        return
    
    print()
    
    # 2. Bağımlılık kontrolü
    if not check_dependencies():
        return
    
    print()
    
    # 3. Environment dosyası kontrolü
    if not check_env_file():
        print("\n📝 Lütfen .env dosyasını düzenleyin ve OPENAI_API_KEY'i ayarlayın!")
        print("   Sonra scripti tekrar çalıştırın.")
        return
    
    print()
    
    # 4. Sunucuyu başlat
    server_process = start_server()
    if not server_process:
        return
    
    print()
    print("🎉 Platform başarıyla başlatıldı!")
    print()
    print("📋 Kullanılabilir komutlar:")
    print("   curl http://localhost:8000/health")
    print("   curl -X POST http://localhost:8000/api/v1/ai/command -H 'Content-Type: application/json' -d '{\"command\": \"Instagram'\''ı test et\"}'")
    print("   python test_ai_platform.py")
    print()
    print("🛑 Sunucuyu durdurmak için Ctrl+C")
    
    try:
        # Sunucuyu çalışır durumda tut
        server_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Sunucu durduruluyor...")
        server_process.terminate()
        print("✅ Sunucu durduruldu")

if __name__ == "__main__":
    main() 