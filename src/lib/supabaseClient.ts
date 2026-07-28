// src/lib/supabaseClient.ts — 浏览器端 Supabase 客户端
import { createClient } from '@supabase/supabase-js';

export const supabaseUrl = import.meta.env.PUBLIC_SUPABASE_URL as string;
export const supabaseAnonKey = import.meta.env.PUBLIC_SUPABASE_ANON_KEY as string;

export const supabase = supabaseUrl && supabaseAnonKey
  ? createClient(supabaseUrl, supabaseAnonKey)
  : null;

if (!supabase) {
  console.warn('[LifeOS] Supabase 未配置：请设置 PUBLIC_SUPABASE_URL / PUBLIC_SUPABASE_ANON_KEY');
}
