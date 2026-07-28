// src/lib/supabase.ts — Supabase 浏览器端客户端
export const supabaseUrl = import.meta.env.PUBLIC_SUPABASE_URL as string;
export const supabaseAnonKey = import.meta.env.PUBLIC_SUPABASE_ANON_KEY as string;

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn('[LifeOS] Supabase 未配置：请设置 PUBLIC_SUPABASE_URL 和 PUBLIC_SUPABASE_ANON_KEY');
}
