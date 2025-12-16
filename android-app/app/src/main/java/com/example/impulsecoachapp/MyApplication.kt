// app.MyApplication
package com.example.impulsecoachapp

import android.app.Application
import android.util.Log
import androidx.hilt.work.HiltWorkerFactory
import androidx.work.Configuration
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import com.example.impulsecoachapp.utils.NotificationHelper
import com.example.impulsecoachapp.worker.DailyHomeworkWorker
import dagger.hilt.android.HiltAndroidApp
import java.util.concurrent.TimeUnit
import java.util.Calendar
import javax.inject.Inject

@HiltAndroidApp
class MyApplication : Application(), Configuration.Provider { // 1. Configuration.Provider 인터페이스 구현

    // 2. Hilt가 만든 Worker 공장을 주입받음
    @Inject lateinit var workerFactory: HiltWorkerFactory

    // 3. WorkManager가 이 설정을 보고 Hilt 사용
    override val workManagerConfiguration: Configuration
        get() = Configuration.Builder()
            .setWorkerFactory(workerFactory)
            .build()

    override fun onCreate() {
        super.onCreate() // 4. 부모 클래스(Hilt 생성 코드)의 onCreate를 먼저 실행
        // 5. 알림 채널 생성 (앱 켜질 때 한 번만 해두면 됨)
        NotificationHelper.createNotificationChannel(this)
        // 6. 매일 과제 알림 스케줄링
        setupDailyNotification()
    }

    private fun setupDailyNotification() {
        // 1. 아침 9시까지 얼마나 기다려야 하는지 계산
        val delayDiff = calculateDelayForNextTargetTime(9) // 9시로 설정 (24시간제)

        // 2. 작업 생성 (24시간 주기 + 초기 지연 시간 설정)
        val dailyRequest = PeriodicWorkRequestBuilder<DailyHomeworkWorker>(24, TimeUnit.HOURS)
            .setInitialDelay(delayDiff, TimeUnit.MILLISECONDS)
            .addTag("DailyHomework") // 태그 추가 (관리 용이)
            .build()

        // 3. 작업 예약
        // 주의: 기존에 등록된 작업의 시간 설정을 바꾸려면 KEEP 대신 UPDATE를 쓰거나,
        // 앱을 삭제 후 재설치해야 적용됩니다.
        WorkManager.getInstance(this).enqueueUniquePeriodicWork(
            "DailyHomework",
            ExistingPeriodicWorkPolicy.KEEP,
            dailyRequest
        )

        Log.d("MyApplication", "매일 과제 알림이 오전 9시로 예약되었습니다.")
    }

    /**
     * 다음 타겟 시간(예: 오전 9시)까지 남은 시간(ms)을 계산하는 함수
     * @param targetHour: 0 ~ 23 (24시간제)
     */
    private fun calculateDelayForNextTargetTime(targetHour: Int): Long {
        val currentTime = Calendar.getInstance()
        val targetTime = Calendar.getInstance().apply {
            set(Calendar.HOUR_OF_DAY, targetHour)
            set(Calendar.MINUTE, 0)
            set(Calendar.SECOND, 0)
            set(Calendar.MILLISECOND, 0)
        }

        // 만약 오늘 이미 9시가 지났다면, 내일 9시로 설정
        if (targetTime.before(currentTime)) {
            targetTime.add(Calendar.DAY_OF_YEAR, 1)
        }

        // 남은 시간 = 타겟 시간 - 현재 시간
        return targetTime.timeInMillis - currentTime.timeInMillis
    }
}
