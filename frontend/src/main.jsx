import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './tokens.css'
import LoginPage from './pages/LoginPage'
import SignUpPage from './pages/SignUpPage'
import IntakePage from './pages/IntakePage'
import ResultPage from './pages/ResultPage'
import DashboardPage from './pages/DashboardPage'
import AdminPage from './pages/AdminPage'
import PatientDashboardPage from './pages/PatientDashboardPage'
import ClinicalPage from './pages/ClinicalPage'
import Layout from './components/Layout'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/signup" element={<SignUpPage />} />
        <Route element={<Layout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/dashboard/patient" element={<PatientDashboardPage />} />
          <Route path="/dashboard/doctor" element={<ClinicalPage />} />
          <Route path="/admin" element={<AdminPage />} />
          <Route path="/intake" element={<IntakePage />} />
          <Route path="/result" element={<ResultPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
)
