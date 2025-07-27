// frontend/src/api/parkingApiService.ts
import {
  ViolationSummaryResponse,
  PaginatedViolationEventsResponse,
  PaginatedTopBranchResponse
} from '../types/parkingViolation';


// อ่าน URL ของ Backend จาก .env
const API_BASE_URL = process.env.REACT_APP_API_URL;

// สร้าง Interface สำหรับ Filters เพื่อความปลอดภัยของ Type
export interface ViolationFilters {
  branchId?: string;
  startDate?: string; // Format: YYYY-MM-DD
  endDate?: string;   // Format: YYYY-MM-DD
  isViolationOnly?: boolean;
}

/**
 * ฟังก์ชันสำหรับดึงข้อมูลสรุป (KPI, Chart, Top Branches)
 * @param filters - Object ที่มีเงื่อนไขการกรอง
 */
export const fetchViolationSummary = async (filters: ViolationFilters): Promise<ViolationSummaryResponse> => {
  // สร้าง URLSearchParams เพื่อจัดการ Query String อย่างปลอดภัย
  const params = new URLSearchParams();
  if (filters.branchId) params.append('branch_id', filters.branchId);
  if (filters.startDate) params.append('start_date', filters.startDate);
  if (filters.endDate) params.append('end_date', filters.endDate);

  const queryString = params.toString();

  // นำ queryString ไปต่อท้าย URL
  const response = await fetch(`${API_BASE_URL}/parking_violations/summary?${queryString}`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch violation summary');
  }
  return response.json();
};

//ฟังก์ชันสำหรับดึงข้อมูลสรุป Top Branches ทั้งหมด
export const fetchAllBranchViolations = async (page: number, filters: ViolationFilters): Promise<PaginatedTopBranchResponse> => {
  const params = new URLSearchParams();
  if (filters.startDate) params.append('start_date', filters.startDate);
  if (filters.endDate) params.append('end_date', filters.endDate);
  
  const response = await fetch(`${API_BASE_URL}/parking_violations/all_branches?page=${page}&limit=10&${params.toString()}`);
  if (!response.ok) {
    throw new Error('Failed to fetch all branch violations');
  }
  return response.json();
};

/**
 * ฟังก์ชันสำหรับดึงข้อมูลรายการเหตุการณ์ (สำหรับตาราง)
 * @param page - เลขหน้า
 * @param limit - จำนวนรายการต่อหน้า
 * @param filters - Object ที่มีเงื่อนไขการกรอง
 */
export const fetchViolationEvents = async (page: number, limit: number, filters: ViolationFilters): Promise<PaginatedViolationEventsResponse> => {
  // สร้าง URLSearchParams เช่นกัน
  const params = new URLSearchParams();
  if (filters.branchId) params.append('branch_id', filters.branchId);
  if (filters.startDate) params.append('start_date', filters.startDate);
  if (filters.endDate) params.append('end_date', filters.endDate);
  if (filters.isViolationOnly) params.append('is_violation_only', 'true');

  const queryString = params.toString();
  
  // นำ queryString ไปต่อท้าย URL
  const response = await fetch(`${API_BASE_URL}/parking_violations/events?page=${page}&limit=${limit}&${queryString}`);

  if (!response.ok) {
    throw new Error('Failed to fetch violation events');
  }
  return response.json();
};