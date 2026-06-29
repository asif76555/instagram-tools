#!/bin/bash
# Instagram OTP Tool - Termux Auto Installer

echo "🚀 Installing Instagram OTP Tool..."
echo ""

# Update packages
echo "📦 Updating packages..."
pkg update -y

# Install Python and Git
echo "🐍 Installing Python..."
pkg install python git -y

# Install requirements
echo "📥 Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Installation Complete!"
echo "🎯 Run: python main.py"