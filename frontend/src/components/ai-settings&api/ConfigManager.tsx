// src/components/ConfigManager.tsx
import React, { useState, useEffect } from 'react';
import {
  Settings,
  Camera,
  Monitor,
  Clock,
  // Download,
  Plus,
  Trash2,
  Save,
  AlertTriangle,
  Cpu,
  Edit2 // เพิ่ม Edit2 สำหรับปุ่มจัดการ ROI
} from 'lucide-react';
import { useNavigate } from 'react-router-dom'; // Import useNavigate
import AILogConsole from "./AILogConsole";
const API_BASE_URL = process.env.REACT_APP_API_URL;

// === การกำหนดประเภท (Type Definitions) ===
// กำหนดโครงสร้างสำหรับ Video Source แต่ละตัว
interface VideoSource {
  name: string;
  branch: string;
  source_path: string;
  parking_zone_file: string;
  branch_id: string;
  camera_id: string;
}
interface DebugSettings {
  enabled: boolean
  mock_warning_minutes: number
  mock_violation_minutes: number
}
interface PerformanceSettings {
  target_inference_width: number
  frames_to_skip: number
  draw_bounding_box: boolean
}

// แก้ไขให้ตรงกับ Backend
interface Config {
  model_path: string;
  yolo_model: string;
  img_size: number[]; // ต้องเป็น Array ของตัวเลข
  conf_threshold: number; // ต้องเป็นตัวเลข
  iou_threshold: number; // ต้องเป็นตัวเลข
  reid_model: string;
  boxmot_config_path: string;
  detection_confidence_threshold: number; // ต้องเป็นตัวเลข
  car_class_id: number[]; // ต้องเป็น Array ของตัวเลข
  tracking_method: string;
  per_class_tracking: boolean;
  debug_settings: DebugSettings;
  parking_time_limit_minutes: number;
  parking_time_threshold_seconds: number;
  grace_period_frames_exit: number;
  parked_car_timeout_seconds: number;
  movement_threshold_px: number;
  movement_frame_window: number;
  output_dir: string;
  device: string;
  half_precision: boolean;
  api_key: string;
  display_combined_max_width: number;
  display_combined_max_height: number;
  queue_max_size: number;
  save_video: boolean;
  save_mot_results: boolean;
  enable_brightness_adjustment: boolean;
  brightness_method: string;
  video_sources: VideoSource[];
  performance_settings: PerformanceSettings;
}

// กำหนดโครงสร้างสำหรับ Saved Configs
interface SavedConfig {
  name: string;
  config: Config;
  timestamp: string;
}

// กำหนด props สำหรับแต่ละ Component ย่อย
interface TabButtonProps {
  label: string;
  icon: React.ElementType;
  isActive: boolean;
  onClick: () => void;
}

interface InputFieldProps {
  label: string;
  value: string | number;
  onChange: (value: string | number) => void;
  type?: "text" | "number";
  className?: string;
}

interface SelectFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
  className?: string;
}

interface CheckboxFieldProps {
  label: string;
  value: boolean;
  onChange: (value: boolean) => void;
  className?: string;
}

// === Component ย่อยที่ปรับแก้ Props แล้ว ===
const TabButton: React.FC<TabButtonProps> = ({ label, icon: Icon, isActive, onClick }) => (
  <button
    onClick={onClick}
    className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
      isActive
        ? 'bg-blue-600 text-white shadow-lg'
        : 'bg-gray-100 text-gray-600 hover:bg-gray-200 hover:text-gray-800'
    }`}
  >
    <Icon size={18} />
    <span>{label}</span>
  </button>
);

const InputField: React.FC<InputFieldProps> = ({ label, value, onChange, type = "text", className = "" }) => (
  <div className={`mb-4 ${className}`}>
    <label className="block text-sm font-medium text-gray-700 mb-2">{label}</label>
    <input
      type={type}
      value={value}
      // เพิ่มการตรวจสอบและแปลงค่าสำหรับ 'number' และ 'text'
      onChange={(e) => {
        const inputValue = e.target.value;
        if (type === 'number') {
          onChange(parseFloat(inputValue) || 0); // แปลงเป็นตัวเลข
        } else {
          onChange(inputValue); // คงเป็น String
        }
      }}
      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
    />
  </div>
);

const SelectField: React.FC<SelectFieldProps> = ({ label, value, onChange, options, className = "" }) => (
  <div className={`mb-4 ${className}`}>
    <label className="block text-sm font-medium text-gray-700 mb-2">{label}</label>
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
    >
      {options.map(option => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  </div>
);

const CheckboxField: React.FC<CheckboxFieldProps> = ({ label, value, onChange, className = "" }) => (
  <div className={`mb-4 ${className}`}>
    <label className="flex items-center space-x-2 cursor-pointer">
      <input
        type="checkbox"
        checked={value}
        onChange={(e) => onChange(e.target.checked)}
        className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
      />
      <span className="text-sm font-medium text-gray-700">{label}</span>
    </label>
  </div>
);

// === Component หลัก ===
const ConfigManager: React.FC = () => {
  const navigate = useNavigate(); // ใช้ hook useNavigate
  // useState สำหรับเก็บค่า config
  const [config, setConfig] = useState<Config | null>(null); // ตั้งค่าเริ่มต้นเป็น null เพื่อรอข้อมูลจาก backend
  const [activeTab, setActiveTab] = useState<string>('model');
  const [savedConfigs, setSavedConfigs] = useState<SavedConfig[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  // const [aiRunning, setAiRunning] = useState(false);

  // ดึงค่า config จาก Backend เมื่อ Component ถูกโหลดครั้งแรก
  useEffect(() => {
    const fetchConfig = async () => {
      try {
        // เปลี่ยน URL ตรงนี้ให้เป็นแบบ Relative เพื่อให้ Vite Proxy ทำงาน
        const response = await fetch(`${API_BASE_URL}/api/config`);
        // const response = await fetch('/api/config');
        const backendConfig: Config = await response.json();
        // เพิ่มบรรทัดนี้เพื่อกำหนดค่าเริ่มต้นสำหรับ yolo_model
        if (!backendConfig.yolo_model) {
          backendConfig.yolo_model = 'yolo12n.pt'; // กำหนดค่าเริ่มต้นเป็น yolo12n.pt
        }
        setConfig(backendConfig);
      } catch (err: any) {
        console.error("Error fetching config:", err);
        setError("ไม่สามารถเชื่อมต่อกับ Backend ได้ โปรดตรวจสอบว่า FastAPI Server ทำงานอยู่");
      } finally {
        setLoading(false);
      }
    };
    fetchConfig();

    const saved = localStorage.getItem('ai-configs');
    if (saved) {
      setSavedConfigs(JSON.parse(saved));
    }
  }, []);

  const updateConfig = (path: string, value: any) => {
    setConfig(prev => {
      if (!prev) return null;
      const newConfig = { ...prev };
      const keys = path.split('.');
      let current: any = newConfig;

      for (let i = 0; i < keys.length - 1; i++) {
        if (!(keys[i] in current)) {
          current[keys[i]] = {};
        }
        current = current[keys[i]];
      }

      // ตรวจสอบและแปลงค่าสำหรับ List
      if (path === 'car_class_id' || path === 'img_size') {
        // Assume value is a string like "0,1,2"
        const numbers = (value as string).split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id));
        current[keys[keys.length - 1]] = numbers;
      } else {
        current[keys[keys.length - 1]] = value;
      }

      return newConfig;
    });
  };

  const addVideoSource = () => {
    if (!config) return;
    const newSource: VideoSource = { // ระบุ type ของ newSource
      name: `camera_${config.video_sources.length + 1}`,
      branch: "",
      source_path: "",
      parking_zone_file: "",
      branch_id: "",
      camera_id: ""
    };

    setConfig(prev => ({
      ...(prev as Config),
      video_sources: [...(prev as Config).video_sources, newSource]
    }));
  };

  const removeVideoSource = (index: number) => {
    setConfig(prev => ({
      ...(prev as Config),
      video_sources: (prev as Config).video_sources.filter((_, i) => i !== index)
    }));
  };

  const updateVideoSource = (index: number, field: keyof VideoSource, value: string) => {
    setConfig(prev => ({
      ...(prev as Config),
      video_sources: (prev as Config).video_sources.map((source, i) =>
        i === index ? { ...source, [field]: value } : source
      )
    }));
  };
//   const startAI = async () => {
//   try {
//     const res = await fetch("http://localhost:8000/api/ai/start", { method: "POST" });
//     if (!res.ok) throw new Error("ไม่สามารถเริ่ม AI ได้");
//     setAiRunning(true);
//     alert("✅ AI Started");
//   } catch (err: any) {
//     alert(`❌ Error: ${err.message}`);
//   }
// };

// const stopAI = async () => {
//   if (!window.confirm("คุณแน่ใจหรือไม่ว่าจะหยุด AI?")) return;
//   try {
//     const res = await fetch("http://localhost:8000/api/ai/stop", { method: "POST" });
//     if (!res.ok) throw new Error("ไม่สามารถหยุด AI ได้");
//     setAiRunning(false);
//     alert("🛑 AI Stopped");
//   } catch (err: any) {
//     alert(`❌ Error: ${err.message}`);
//   }
// };

  const generateYAML = (): string => {
    if (!config) return "";
    let yaml = `# config.yaml

# YOLO Model Settings
model_path: ${config.model_path}
yolo_model: "${config.yolo_model}"
img_size: [${config.img_size.join(', ')}]
conf_threshold: ${config.conf_threshold}
iou_threshold: ${config.iou_threshold}

# Re-ID Model Settings
reid_model: "${config.reid_model}"
boxmot_config_path: ${config.boxmot_config_path}
detection_confidence_threshold: ${config.detection_confidence_threshold}
car_class_id: [${config.car_class_id.join(', ')}]

# Tracking Method
tracking_method: "${config.tracking_method}"
per_class_tracking: ${config.per_class_tracking}

# Debug Settings
debug_settings:
  enabled: ${config.debug_settings.enabled}
  mock_warning_minutes: ${config.debug_settings.mock_warning_minutes}
  mock_violation_minutes: ${config.debug_settings.mock_violation_minutes}

# Parking Thresholds
parking_time_limit_minutes: ${config.parking_time_limit_minutes}
parking_time_threshold_seconds: ${config.parking_time_threshold_seconds}
grace_period_frames_exit: ${config.grace_period_frames_exit}
parked_car_timeout_seconds: ${config.parked_car_timeout_seconds}

# Movement Detection
movement_threshold_px: ${config.movement_threshold_px}
movement_frame_window: ${config.movement_frame_window}

# Output Settings
output_dir: "${config.output_dir}"

# Hardware Settings
device: "${config.device}"
half_precision: ${config.half_precision}

# API Key
api_key: "${config.api_key}"

# Display Settings
display_combined_max_width: ${config.display_combined_max_width}
display_combined_max_height: ${config.display_combined_max_height}

# Queue Settings
queue_max_size: ${config.queue_max_size}

# Save Settings
save_video: ${config.save_video}
save_mot_results: ${config.save_mot_results}

# Brightness Adjustment
enable_brightness_adjustment: ${config.enable_brightness_adjustment}
brightness_method: ${config.brightness_method}

# Video Sources
video_sources:
${config.video_sources.map(source => `  - name: "${source.name}"
    branch: "${source.branch}"
    source_path: "${source.source_path}"
    parking_zone_file: "${source.parking_zone_file}"
    branch_id: "${source.branch_id}"
    camera_id: "${source.camera_id}"`).join('\n')}

# Performance Settings
performance_settings:
  target_inference_width: ${config.performance_settings.target_inference_width}
  frames_to_skip: ${config.performance_settings.frames_to_skip}
  draw_bounding_box: ${config.performance_settings.draw_bounding_box}
`;

    return yaml;
  };

  // const downloadConfig = () => {
  //   const yaml = generateYAML();
  //   const blob = new Blob([yaml], { type: 'text/yaml' });
  //   const url = URL.createObjectURL(blob);
  //   const a = document.createElement('a');
  //   a.href = url;
  //   a.download = 'config.yaml';
  //   document.body.appendChild(a);
  //   a.click();
  //   document.body.removeChild(a);
  //   URL.revokeObjectURL(url);
  // };

  const saveConfigToBackend = async () => {
    if (!config) return;

    try {
      const response = await fetch(`${API_BASE_URL}/api/config`, {
      // const response = await fetch('http://localhost:8000/api/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        // เพิ่มโค้ดส่วนนี้เพื่อดึงข้อผิดพลาดจาก Backend
        const errorData = await response.json();
        const errorMessage = errorData.detail
          ? JSON.stringify(errorData.detail, null, 2)
          : 'Failed to save config to backend';
        throw new Error(errorMessage);
      }

      alert('การตั้งค่าถูกบันทึกที่ Backend เรียบร้อยแล้ว!');
    } catch (err: any) {
      console.error("Error saving config:", err);
      // แสดงข้อความผิดพลาดที่ละเอียดขึ้นจาก Backend
      alert(`เกิดข้อผิดพลาดในการบันทึกการตั้งค่า!\nรายละเอียด: ${err.message}`);
    }
  };

  const loadConfig = (savedConfig: SavedConfig) => {
    setConfig(savedConfig.config);
  };

  const handleManageRoi = (cameraId: string) => {
    // ตรวจสอบว่า cameraId มีค่าก่อนที่จะ navigate
    if (cameraId) {
      navigate(`/roi/${cameraId}`); // นำทางไปยังหน้าวาด ROI
    } else {
      alert('ไม่พบ Camera ID สำหรับกล้องนี้');
    }
  };

  // เพิ่มส่วนแสดงผลเมื่อโหลดอยู่หรือเกิดข้อผิดพลาด
  if (loading) {
      return <div className="text-center p-16">กำลังโหลดการตั้งค่า...</div>;
  }

  if (error) {
      return <div className="text-center p-16 text-red-600">{error}</div>;
  }

  // ตรวจสอบว่า config ไม่ใช่ null ก่อนแสดงผล
  if (!config) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-4">
            AI Car Parking Monitor
          </h1>
          <p className="text-xl text-gray-600">ตั้งค่าระบบตรวจสอบที่จอดรถอัจฉริยะ</p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap justify-center gap-4 mb-8">
          <div className="container mx-auto p-6 space-y-6">
            {/* ส่วนอื่น ๆ ของ ConfigManager */}
            <AILogConsole />
          </div>
        </div>

        {/* Saved Configurations */}
        {savedConfigs.length > 0 && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">การตั้งค่าที่บันทึกไว้</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {savedConfigs.map((savedConfig, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <h4 className="font-medium text-gray-800">{savedConfig.name}</h4>
                  <p className="text-sm text-gray-500 mb-3">
                    {new Date(savedConfig.timestamp).toLocaleString('th-TH')}
                  </p>
                  <button
                    onClick={() => loadConfig(savedConfig)}
                    className="w-full bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition-colors"
                  >
                    โหลดการตั้งค่า
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="flex flex-wrap justify-center gap-2 mb-8 bg-white rounded-xl shadow-lg p-4">
          <TabButton
            label="โมเดล AI"
            icon={Settings}
            isActive={activeTab === 'model'}
            onClick={() => setActiveTab('model')}
          />
          <TabButton
            label="กล้อง"
            icon={Camera}
            isActive={activeTab === 'cameras'}
            onClick={() => setActiveTab('cameras')}
          />
          <TabButton
            label="การจอดรถ"
            icon={Clock}
            isActive={activeTab === 'parking'}
            onClick={() => setActiveTab('parking')}
          />
          <TabButton
            label="ประสิทธิภาพ"
            icon={Cpu}
            isActive={activeTab === 'performance'}
            onClick={() => setActiveTab('performance')}
          />
          <TabButton
            label="การแสดงผล"
            icon={Monitor}
            isActive={activeTab === 'display'}
            onClick={() => setActiveTab('display')}
          />
          <button
            onClick={saveConfigToBackend}
            className="ml-auto flex items-center space-x-2 bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition-colors shadow-lg"
          >
            <Save size={20} />
            <span>บันทึกการตั้งค่า</span>
          </button>
        </div>

        {/* Tab Content */}
        <div className="bg-white rounded-xl shadow-lg p-8">
          {activeTab === 'model' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-gray-800 mb-6">การตั้งค่าโมเดล AI</h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* <InputField
                  label="Path ของโมเดล YOLO"
                  value={config.model_path}
                  onChange={(value) => updateConfig('model_path', value)}
                /> */}

                <SelectField
                  label="โมเดล YOLO"
                  value={config.yolo_model}
                  onChange={(value) => updateConfig('yolo_model', value)}
                  options={[
                    { value: 'yolo12n.pt', label: 'YOLO12 Nano (เร็วที่สุด แต่ไม่แม่นยำมาก)' },
                    { value: 'yolo12s.pt', label: 'YOLO12 Small (เร็วเล็กน้อย ความแม่นยำน้อย)' },
                    { value: 'yolo12m.pt', label: 'YOLO12 Medium (ระดับกลาง)' },
                    { value: 'yolo12l.pt', label: 'YOLO12 Large (ช้า แต่ความแม่ยำสูง)' }
                  ]}
                />

                {/* <InputField
                  label="ขนาดภาพที่ป้อนโมเดล"
                  value={config.img_size[0]}
                  onChange={(value) => updateConfig('img_size', [value as number, value as number])}
                  type="number"
                />Path ของไฟล์วิดีโอ
                 */}
                {/* <InputField
                  label="Confidence Threshold"
                  value={config.conf_threshold}
                  onChange={(value) => updateConfig('conf_threshold', value)}
                  type="number"
                />

                <InputField
                  label="IOU Threshold"
                  value={config.iou_threshold}
                  onChange={(value) => updateConfig('iou_threshold', value)}
                  type="number"
                />
                 */}
                <SelectField
                  label="อุปกรณ์ที่ใช้"
                  value={config.device}
                  onChange={(value) => updateConfig('device', value)}
                  options={[
                    { value: 'cpu', label: 'CPU' },
                    { value: 'cuda', label: 'GPU (CUDA)' }
                  ]}
                />
              </div>

              {/* <div className="border-t pt-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">การติดตามวัตถุ (Tracking)</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <InputField
                    label="โมเดล Re-ID"
                    value={config.reid_model}
                    onChange={(value) => updateConfig('reid_model', value)}
                  />

                  <SelectField
                    label="วิธีการติดตาม"
                    value={config.tracking_method}
                    onChange={(value) => updateConfig('tracking_method', value)}
                    options={[
                      { value: 'deepocsort', label: 'DeepOCSORT' },
                      { value: 'botsort', label: 'BotSORT' },
                      { value: 'strongsort', label: 'StrongSORT' }
                    ]}
                  />

                  <InputField
                    label="Detection Confidence Threshold"
                    value={config.detection_confidence_threshold}
                    onChange={(value) => updateConfig('detection_confidence_threshold', value)}
                    type="number"
                  />

                  <InputField
                    label="Car Class IDs (คั่นด้วยจุลภาค)"
                    value={config.car_class_id.join(', ')} // แปลงเป็น String ก่อนแสดงผล
                    onChange={(value) => updateConfig('car_class_id', value)} // updateConfig จะแปลงกลับเป็น Array ให้
                  />
                </div>
              </div> */}

              <div className="border-t pt-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">การตั้งค่าดีบัก</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <CheckboxField
                    label="เปิดโหมดดีบัก (จำลองการทำงานที่เร็วขึ้น)"
                    value={config.debug_settings.enabled}
                    onChange={(value) => updateConfig('debug_settings.enabled', value)}
                  />
{/*
                  <InputField
                    label="เวลาแจ้งเตือน (นาที)"
                    value={config.debug_settings.mock_warning_minutes}
                    onChange={(value) => updateConfig('debug_settings.mock_warning_minutes', value)}
                    type="number"
                  /> */}

                  <InputField
                    label="เวลาฝ่าฝืน (นาที)"
                    value={config.debug_settings.mock_violation_minutes}
                    onChange={(value) => updateConfig('debug_settings.mock_violation_minutes', value)}
                    type="number"
                  />
                </div>
              </div>
            </div>
          )}

          {activeTab === 'cameras' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold text-gray-800">การตั้งค่ากล้อง</h2>
                <button
                  onClick={addVideoSource}
                  className="flex items-center space-x-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
                >
                  <Plus size={18} />
                  <span>เพิ่มกล้อง</span>
                </button>
              </div>

              {config.video_sources.map((source, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-6 mb-4 relative">
                  <div className="flex justify-between items-start mb-4">
                    <h4 className="font-semibold text-lg text-gray-800">กล้อง #{index + 1} ({source.name})</h4>
                    <div className="flex space-x-2">
                        <button
                            onClick={() => handleManageRoi(source.camera_id)}
                            className="flex items-center px-3 py-1 bg-purple-500 text-white rounded-md text-sm hover:bg-purple-600 transition-colors"
                            aria-label="Manage ROI"
                        >
                            <Edit2 size={16} className="mr-1" /> จัดการ ROI
                        </button>
                        {config.video_sources.length > 1 && (
                            <button
                                onClick={() => removeVideoSource(index)}
                                className="text-red-500 hover:text-red-700 transition-colors"
                                aria-label="Remove video source"
                            >
                                <Trash2 size={20} />
                            </button>
                        )}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <InputField
                      label="ชื่อกล้อง"
                      value={source.name}
                      onChange={(value) => updateVideoSource(index, 'name', value as string)}
                    />

                    <InputField
                      label="สาขา"
                      value={source.branch}
                      onChange={(value) => updateVideoSource(index, 'branch', value as string)}
                    />

                    <InputField
                      label="Path วิดีโอจากกล้อง"
                      value={source.source_path}
                      onChange={(value) => updateVideoSource(index, 'source_path', value as string)}
                    />

                    <InputField
                      label="ไฟล์ Parking Zone"
                      value={source.parking_zone_file}
                      onChange={(value) => updateVideoSource(index, 'parking_zone_file', value as string)}
                    />

                    <InputField
                      label="Branch ID"
                      value={source.branch_id}
                      onChange={(value) => updateVideoSource(index, 'branch_id', value as string)}
                    />

                    <InputField
                      label="Camera ID"
                      value={source.camera_id}
                      onChange={(value) => updateVideoSource(index, 'camera_id', value as string)}
                      className="md:col-span-2"
                    />
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'parking' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-gray-800 mb-6">การตั้งค่าการจอดรถ</h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <InputField
                  label="เวลาจอดสูงสุด (นาที)"
                  value={config.parking_time_limit_minutes}
                  onChange={(value) => updateConfig('parking_time_limit_minutes', value)}
                  type="number"
                />

                {/* <InputField
                  label="เวลาขั้นต่ำที่จะถือว่าจอด (วินาที)"
                  value={config.parking_time_threshold_seconds}
                  onChange={(value) => updateConfig('parking_time_threshold_seconds', value)}
                  type="number"
                />

                <InputField
                  label="Grace Period Frames (เฟรมที่ยอมให้ออกนอกโซน)"
                  value={config.grace_period_frames_exit}
                  onChange={(value) => updateConfig('grace_period_frames_exit', value)}
                  type="number"
                />

                <InputField
                  label="Timeout รถจอด (วินาที)"
                  value={config.parked_car_timeout_seconds}
                  onChange={(value) => updateConfig('parked_car_timeout_seconds', value)}
                  type="number"
                />

                <InputField
                  label="Movement Threshold (พิกเซล)"
                  value={config.movement_threshold_px}
                  onChange={(value) => updateConfig('movement_threshold_px', value)}
                  type="number"
                />

                <InputField
                  label="Movement Frame Window"
                  value={config.movement_frame_window}
                  onChange={(value) => updateConfig('movement_frame_window', value)}
                  type="number"
                /> */}
              </div>

              <div className="border-t pt-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">การตั้งค่าอื่นๆ</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* <InputField
                    label="API Key"
                    value={config.api_key}
                    onChange={(value) => updateConfig('api_key', value)}
                  /> */}

                  <InputField
                    label="Output Directory(ดูผลที่บันทึกไว้)"
                    value={config.output_dir}
                    onChange={(value) => updateConfig('output_dir', value)}
                  />

                  <div className="md:col-span-2 grid grid-cols-2 md:grid-cols-4 gap-4">
                    <CheckboxField
                      label="บันทึกวิดีโอ"
                      value={config.save_video}
                      onChange={(value) => updateConfig('save_video', value)}
                    />

                    <CheckboxField
                      label="บันทึกผล MOT"
                      value={config.save_mot_results}
                      onChange={(value) => updateConfig('save_mot_results', value)}
                    />

                    <CheckboxField
                      label="ปรับความสว่าง"
                      value={config.enable_brightness_adjustment}
                      onChange={(value) => updateConfig('enable_brightness_adjustment', value)}
                    />

                    <SelectField
                      label="วิธีปรับความสว่าง"
                      value={config.brightness_method}
                      onChange={(value) => updateConfig('brightness_method', value)}
                      options={[
                        { value: 'clahe', label: 'CLAHE' },
                        { value: 'histogram', label: 'Histogram' }
                      ]}
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'performance' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-gray-800 mb-6">การตั้งค่าประสิทธิภาพ</h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <InputField
                  label="ความกว้างของเฟรมที่ส่งเข้าโมเดล"
                  value={config.performance_settings.target_inference_width}
                  onChange={(value) => updateConfig('performance_settings.target_inference_width', value)}
                  type="number"
                />

                <InputField
                  label="จำนวนเฟรมที่ข้าม (1 = ไม่ข้าม)"
                  value={config.performance_settings.frames_to_skip}
                  onChange={(value) => updateConfig('performance_settings.frames_to_skip', value)}
                  type="number"
                />

                {/* <InputField
                  label="ขนาด Queue สูงสุด"
                  value={config.queue_max_size}
                  onChange={(value) => updateConfig('queue_max_size', value)}
                  type="number"
                /> */}

                <CheckboxField
                  label="แสดง Bounding Box(กรอบรอบรถ)"
                  value={config.performance_settings.draw_bounding_box}
                  onChange={(value) => updateConfig('performance_settings.draw_bounding_box', value)}
                />

                <CheckboxField
                  label="Half Precision (GPU เท่านั้น)"
                  value={config.half_precision}
                  onChange={(value) => updateConfig('half_precision', value)}
                />
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex items-start space-x-3">
                  <AlertTriangle className="text-yellow-600 mt-1" size={20} />
                  <div>
                    <h4 className="font-medium text-yellow-800">คำแนะนำการปรับแต่งประสิทธิภาพ</h4>
                    <ul className="mt-2 text-sm text-yellow-700 list-disc list-inside space-y-1">
                      <li>ลด frames_to_skip ถ้าต้องการความแม่นยำสูง (แต่จะช้าลง)</li>
                      <li>เพิ่ม frames_to_skip ถ้าต้องการความเร็วสูง (แต่อาจพลาดเหตุการณ์)</li>
                      <li>ลด target_inference_width สำหรับเครื่องที่ช้า</li>
                      <li>เปิด Half Precision เฉพาะเมื่อใช้ GPU</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'display' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-gray-800 mb-6">การตั้งค่าการแสดงผล</h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <InputField
                  label="ความกว้างสูงสุดของหน้าต่าง"
                  value={config.display_combined_max_width}
                  onChange={(value) => updateConfig('display_combined_max_width', value)}
                  type="number"
                />

                <InputField
                  label="ความสูงสูงสุดของหน้าต่าง"
                  value={config.display_combined_max_height}
                  onChange={(value) => updateConfig('display_combined_max_height', value)}
                  type="number"
                />
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start space-x-3">
                  <Monitor className="text-blue-600 mt-1" size={20} />
                  <div>
                    <h4 className="font-medium text-blue-800">การแสดงผลแบบ Real-time</h4>
                    <p className="mt-2 text-sm text-blue-700">
                      ขนาดหน้าต่างจะปรับอัตโนมัติตามความละเอียดของวิดีโอต้นฉบับ
                      แต่จะไม่เกินค่าสูงสุดที่กำหนดไว้
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Live Preview */}
        <div className="mt-8 bg-white rounded-xl shadow-lg p-8">
          <h3 className="text-xl font-bold text-gray-800 mb-4">ตัวอย่าง YAML ที่จะได้</h3>
          <pre className="bg-gray-100 rounded-lg p-4 overflow-auto text-sm font-mono max-h-96">
            {generateYAML()}
          </pre>
        </div>
      </div>
    </div>
  );
};

export default ConfigManager;