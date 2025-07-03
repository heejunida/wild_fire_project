package com.wild_fire.servlet;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.*;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.PrintWriter;
@WebServlet("/getWeather")
public class NasaWeatherServlet extends HttpServlet {
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {

        // 1. 위/경도 파라미터 받기
        String lat = request.getParameter("lat");
        String lng = request.getParameter("lng");

        // 2. 파이썬 실행 경로 지정
        String pyPath = "/Users/heejunida/Desktop/kg/wildFire1/wild_fire_project/wild_fire_client/data/apiConnect.py";

        // 3. 파이썬 프로세스 실행 명령 준비
        ProcessBuilder pb = new ProcessBuilder("python3", pyPath, lat, lng);

        // 4. 프로세스 실행 및 결과 읽기
        Process process = pb.start();

        // 파이썬 표준 출력 읽기
        BufferedReader stdInput = new BufferedReader(new InputStreamReader(process.getInputStream()));
        StringBuilder sb = new StringBuilder();
        String line;
        while ((line = stdInput.readLine()) != null) {
            sb.append(line).append("\n");
        }

        // 에러 스트림도 읽어보기(문제 추적용)
        BufferedReader stdError = new BufferedReader(new InputStreamReader(process.getErrorStream()));
        StringBuilder errSb = new StringBuilder();
        while ((line = stdError.readLine()) != null) {
            errSb.append(line).append("\n");
        }
        try {
            int exitCode = process.waitFor();

            // 5. 응답 구성
            response.setContentType("application/json; charset=UTF-8");
            PrintWriter out = response.getWriter();
            if (exitCode == 0) {
                // 파이썬에서 json 문자열을 print()로 출력했다고 가정
                out.write(sb.toString());
            } else {
                // 에러
                response.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
                out.write("{\"error\": \"Python error: " + errSb.toString() + "\"}");
            }
            out.flush();
            out.close();
        }
        catch (InterruptedException e) {
            e.printStackTrace();
            response.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
            PrintWriter out = response.getWriter();
            out.write("{\"error\": \"Process interrupted: " + e.getMessage() + "\"}");
            out.flush();
            out.close();
        }
    }
}