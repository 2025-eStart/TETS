// data.local.HomeworkStorage.kt
package com.example.impulsecoachapp.data.local

import android.content.Context
import android.content.SharedPreferences
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class HomeworkStorage @Inject constructor(
    @ApplicationContext context: Context
) {
    private val prefs: SharedPreferences = context.getSharedPreferences("homework_prefs", Context.MODE_PRIVATE)

    // 과제 저장
    fun saveHomework(content: String) {
        prefs.edit().putString("today_homework", content).apply()
    }

    // 과제 불러오기 (저장된 게 없으면 기본 문구 반환)
    fun getHomework(): String {
        return prefs.getString("today_homework", null)
            ?: "여행자님! 오늘도 루시와 약속한 과제를 수행해 보아요! 🦊"
    }

    // 과제 삭제 (새 주차 상담 시작 시)
    fun clearHomework() {
        prefs.edit().remove("today_homework").apply()
    }
}