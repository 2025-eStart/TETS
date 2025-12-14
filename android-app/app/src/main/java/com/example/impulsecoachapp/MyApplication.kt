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
        // 24시간마다 실행되는 작업 생성
        // (테스트할 때는 24시간 대신 15분(TimeUnit.MINUTES)으로 줄여서 확인 가능 - 최소 간격 15분)
        val dailyRequest = PeriodicWorkRequestBuilder<DailyHomeworkWorker>(24, TimeUnit.HOURS)
            .build()

        // 큐에 작업 등록
        // enqueueUniquePeriodicWork: 이미 등록된 "DailyHomework"라는 작업이 있으면
        // KEEP: 유지한다 (새로 등록 안 함 -> 중복 방지)
        // REPLACE: 지우고 새로 등록한다
        WorkManager.getInstance(this).enqueueUniquePeriodicWork(
            "DailyHomework",
            ExistingPeriodicWorkPolicy.KEEP,
            dailyRequest
        )

        Log.d("MyApplication", "매일 과제 알림 작업이 예약되었습니다.")
    }
}
