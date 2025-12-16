// worker.DailyHomeworkWorker.kt
// 주간 상담 완료 후 매일 과제 알림 (10주차 상담 프로그램 완료 전까지만 동작)
package com.example.impulsecoachapp.worker

import android.content.Context
import androidx.hilt.work.HiltWorker
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.example.impulsecoachapp.data.repository.ActualChatRepository
import com.example.impulsecoachapp.utils.NotificationHelper
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject

@HiltWorker
class DailyHomeworkWorker@AssistedInject constructor(
    @Assisted context: Context,
    @Assisted workerParams: WorkerParameters,
    private val repository: ActualChatRepository
) : CoroutineWorker(context, workerParams) {

    override suspend fun doWork(): Result {
        // 오늘 1주차 상담을 막 끝냈다면 알림 스킵
        // (2주차부터는 상담 당일에도 알림이 감)
        if (repository.isFirstWeekSessionToday()) {
            return Result.success()
        }

        // 2. 과제 가져오기
        val homework = repository.getStoredHomework()

        // 3. 신규 유저(과제 없음)면 스킵
        if (homework == null) {
            return Result.success()
        }
        // 4. 알림 내용 구성 (숙제가 없으면 기본 문구)
        val notificationContent = run {
            val baseText = homework.description

            // (나중에 예시 로직을 다시 살릴 때를 대비한 구조)
            /*
            if (homework.examples.isNotEmpty()) {
                "$baseText\n(예: ${homework.examples[0]})"
            } else {
                baseText
            }
            */

            baseText // 이 블록의 최종 반환값 (String)
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