//UI의 상태와 로직
package com.example.impulsecoachapp.viewmodels

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel

// ViewModel이 관리할 UI 상태를 정의하는 데이터 클래스
data class MainUiState(
    val showPermissionDialog: Boolean = false
)

class MainViewModel : ViewModel() {

    // UI 상태를 외부에서는 읽기만 가능하도록, 내부에서는 수정 가능하도록 설정
    var uiState by mutableStateOf(MainUiState())
        private set

    // 권한 확인 결과를 받아 UI 상태를 업데이트하는 함수
    fun onPermissionResult(isGranted: Boolean) {
        uiState = uiState.copy(showPermissionDialog = !isGranted)
    }

    // 다이얼로그가 닫힐 때 호출될 함수
    fun onDialogDismissed() {
        uiState = uiState.copy(showPermissionDialog = false)
    }
}