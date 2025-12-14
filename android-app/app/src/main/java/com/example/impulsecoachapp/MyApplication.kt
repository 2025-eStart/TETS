// app.MyApplication
package com.example.impulsecoachapp

import android.app.Application
import dagger.hilt.android.HiltAndroidApp

@HiltAndroidApp
class MyApplication : Application() {
    // Hilt가 코드를 자동 생성하므로 내부는 비어있어도 됩니다.
}