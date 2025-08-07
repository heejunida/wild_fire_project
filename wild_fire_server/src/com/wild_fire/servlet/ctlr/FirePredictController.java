package com.wild_fire.servlet.ctlr;

import org.json.simple.JSONObject;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

/**
 * 이 서블릿은 사용자의 예측 요청을 받아 Flask API 서버에 전달하고,
 * 그 결과를 다시 프론트엔드로 반환하는 중계자 역할을 합니다.
 * 기존의 복잡한 파이썬 스크립트 실행 및 관리 로직은 모두 Flask 서버로 이전되었습니다.
 */
@WebServlet("/fire-predict")
public class FirePredictController extends HttpServlet {

    private static final String PREDICTION_API_URL = "http://localhost:5001/predict";
    private static final HttpClient httpClient = HttpClient.newBuilder()
            .version(HttpClient.Version.HTTP_1_1)
            .connectTimeout(Duration.ofSeconds(10))
            .build();

    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        
        // POST 요청 본문에서 파라미터를 읽어옵니다.
        String lat = request.getParameter("lat");
        String lng = request.getParameter("lng");
        String fireDate = request.getParameter("fireDate");
        String fireTime = request.getParameter("fireTime");
        String userId = (String) request.getSession().getAttribute("user");

        if (userId == null) {
            response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
            response.getWriter().write("{\"status\":\"error\", \"message\":\"User not logged in\"}");
            return;
        }
        
        if (lat == null || lng == null || fireDate == null || fireTime == null) {
            response.setStatus(HttpServletResponse.SC_BAD_REQUEST);
            response.getWriter().write("{\"status\":\"error\", \"message\":\"Missing required parameters\"}");
            return;
        }

        // Flask API에 보낼 JSON 본문 생성
        JSONObject requestBody = new JSONObject();
        requestBody.put("lat", lat);
        requestBody.put("lng", lng);
        requestBody.put("fireDate", fireDate);
        requestBody.put("fireTime", fireTime);

        try {
            // Flask API 호출 (POST 방식)
            HttpRequest apiRequest = HttpRequest.newBuilder()
                    .uri(URI.create(PREDICTION_API_URL))
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(requestBody.toJSONString()))
                    .timeout(Duration.ofMinutes(5))
                    .build();

            HttpResponse<String> apiResponse = httpClient.send(apiRequest, HttpResponse.BodyHandlers.ofString());

            // 받은 결과를 프론트엔드에 그대로 전달
            response.setContentType("application/json; charset=UTF-8");
            response.setStatus(apiResponse.statusCode());
            response.getWriter().write(apiResponse.body());

        } catch (Exception e) {
            e.printStackTrace();
            response.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
            response.getWriter().write("{\"status\":\"error\", \"message\":\"Failed to communicate with the prediction server.\"}");
        }
    }
}
