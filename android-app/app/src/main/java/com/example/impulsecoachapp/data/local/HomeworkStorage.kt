// data.local.HomeworkStorage.kt
package com.example.impulsecoachapp.data.local

import android.content.Context
import android.content.SharedPreferences
import com.example.impulsecoachapp.domain.model.Homework
import com.google.gson.Gson
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class HomeworkStorage @Inject constructor(
    @ApplicationContext context: Context
) {
    private val prefs: SharedPreferences = context.getSharedPreferences("homework_prefs", Context.MODE_PRIVATE)
    private val gson = Gson() // 객체 직렬화를 위한 Gson 인스턴스

    // 과제 저장 (객체 -> JSON String 변환 후 저장)
    fun saveHomework(homework: Homework) {
        val jsonString = gson.toJson(homework)
        prefs.edit().putString("today_homework_json", jsonString).apply()
    }

    // 과제 불러오기 (JSON String -> 객체 변환)
    fun getHomework(): Homework? {
        val jsonString = prefs.getString("today_homework_json", null) ?: return null

        return try {
            gson.fromJson(jsonString, Homework::class.java)
        } catch (e: Exception) {
            e.printStackTrace()
            null
        }
    }

    // 기본 문구만 필요한 경우를 위한 헬퍼 (알림용 fallback)
    fun getDefaultMessage(): String {
        return "여행자님! 오늘도 루시와 약속한 과제를 수행해 보아요! 🦊"
    }

    // 과제 삭제
    fun clearHomework() {
        prefs.edit().remove("today_homework_json").apply()
    }
}