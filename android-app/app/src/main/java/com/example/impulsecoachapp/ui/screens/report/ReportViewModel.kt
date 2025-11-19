package com.example.impulsecoachapp.ui.screens.report

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.impulsecoachapp.data.Transaction
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.time.LocalDate
import java.time.LocalTime
import java.util.UUID

/*
화면에 필요한 데이터와 상태를 관리하고, 비즈니스 로직을 처리하는 ViewModel
- selectedDate: 현재 선택된 날짜
- transactions: 선택된 날짜의 소비 내역 리스트
- loadTransactions(): 날짜에 맞는 소비 내역을 불러오는 함수 (여기서는 더미 데이터 사용, 추후 FastAPI 연동)
- showCalendar, showDetailSheet: 캘린더와 상세 정보 시트의 노출 여부를 제어
 */

// 화면에 표시될 상태를 관리하는 데이터 클래스
data class ReportUiState(
    val selectedDate: LocalDate = LocalDate.now(),
    val transactions: List<Transaction> = emptyList(),
    val isLoading: Boolean = false,
    val showCalendar: Boolean = false,
    val selectedTransaction: Transaction? = null
)

class ReportViewModel : ViewModel() {

    private val _uiState = MutableStateFlow(ReportUiState())
    val uiState: StateFlow<ReportUiState> = _uiState.asStateFlow()

    init {
        // ViewModel 생성 시 오늘 날짜의 소비 내역을 불러옵니다.
        loadTransactionsForDate(LocalDate.now())
    }

    // 특정 날짜의 소비 내역을 불러옵니다.
    // TODO: 추후 FastAPI와 연동하여 실제 데이터를 가져오는 로직으로 교체해야 합니다.
    fun loadTransactionsForDate(date: LocalDate) {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, selectedDate = date) }

            // (임시) 더미 데이터 생성
            val dummyTransactions = if (date == LocalDate.of(2025, 7, 2)) {
                (1..10).map {
                    Transaction(
                        id = UUID.randomUUID().toString(),
                        time = LocalTime.of(16, 5),
                        description = if (it == 6) "카카오톡 선물" else "배민",
                        amount = 25000,
                        paymentMethod = "신한체크",
                        isImpulseBuy = false
                    )
                }
            } else {
                emptyList() // 다른 날짜는 비어있도록 설정
            }

            _uiState.update {
                it.copy(isLoading = false, transactions = dummyTransactions)
            }
        }
    }

    // 캘린더 표시 상태 변경
    fun toggleCalendar(show: Boolean) {
        _uiState.update { it.copy(showCalendar = show) }
    }

    // 소비 내역 상세 정보 시트 표시
    fun showTransactionDetails(transaction: Transaction) {
        _uiState.update { it.copy(selectedTransaction = transaction) }
    }

    // 상세 정보 시트 닫기
    fun dismissTransactionDetails() {
        _uiState.update { it.copy(selectedTransaction = null) }
    }

    // 충동 소비 체크박스 상태 변경
    fun onImpulseCheckChanged(transaction: Transaction, isChecked: Boolean) {
        // TODO: FastAPI 서버에 변경된 상태를 전송하는 API 호출 로직 추가
        val updatedTransactions = _uiState.value.transactions.map {
            if (it.id == transaction.id) {
                it.copy(isImpulseBuy = isChecked)
            } else {
                it
            }
        }
        _uiState.update { it.copy(transactions = updatedTransactions) }
    }
}

