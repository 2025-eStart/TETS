// worker.WeeklyReminderWorker.kt
// 주간 상담 완료 후 일주일 뒤 상담 알림
package com.example.impulsecoachapp.worker

import android.content.Context
import androidx.hilt.work.HiltWorker
import androidx.work.Worker
import androidx.work.WorkerParameters
import com.example.impulsecoachapp.utils.NotificationHelper
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject

@HiltWorker
class WeeklyReminderWorker @AssistedInject constructor(
    @Assisted context: Context,
    @Assisted workerParams: WorkerParameters
) : Worker(context, workerParams) {

    override fun doWork(): Result {
        NotificationHelper.showNotification(
            applicationContext,
            "주간 상담 알림 📅",
            "주간 상담을 할 날이에요! 앱에 접속해서 상담을 진행해주세요."
        )
        return Result.success()
    }
}