// worker.DailyHomeworkWorker.kt
// 주간 상담 완료 후 매일 과제 알림 (10주차 상담 프로그램 완료 전까지만 동작)
package com.example.impulsecoachapp.worker

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.example.impulsecoachapp.data.repository.ActualChatRepository
import com.example.impulsecoachapp.utils.NotificationHelper

class DailyHomeworkWorker(
    context: Context,
    workerParams: WorkerParameters,
    private val repository: ActualChatRepository
) : CoroutineWorker(context, workerParams) {

    override suspend fun doWork(): Result {
        // 1. Repository를 통해 저장된 숙제 객체 가져오기
        val homework = repository.getStoredHomework()

        // 2. 알림 내용 구성 (숙제가 없으면 기본 문구)
        val notificationContent = if (homework != null) {
            // 알림창은 공간이 좁으므로 설명만 보여줌. 예시 생략
            val baseText = homework.description
            baseText
            /*
            if (homework.examples.isNotEmpty()) {
                "$baseText\n(예: ${homework.examples[0]})"
            } else {
                baseText
            }
             */
        } else {
            "여행자님! 오늘도 루시와 약속한 과제를 수행해 보아요! 🦊"
        }

        // 3. 알림 띄우기
        NotificationHelper.showNotification(
            applicationContext,
            "오늘의 과제 도착 📬",
            notificationContent
        )

        return Result.success()
    }
}