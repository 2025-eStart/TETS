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
        // 1. Repository를 통해 로컬에 저장된 과제 가져오기
        // (Repository가 HomeworkStorage를 호출)
        val homeworkContent = repository.getStoredHomework()

        // 2. 알림 띄우기

        NotificationHelper.showNotification(
            applicationContext,
            "오늘의 과제 도착 📬",
            homeworkContent
        )

        return Result.success()
    }
}