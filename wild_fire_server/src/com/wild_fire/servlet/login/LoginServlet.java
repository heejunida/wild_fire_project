package com.wild_fire.servlet.login;

import com.wild_fire.service.LoginSrvc;
import org.json.simple.JSONObject;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;
import java.io.IOException;

@WebServlet("/login")
public class LoginServlet extends HttpServlet {

    private final LoginSrvc loginSrvc = new LoginSrvc();

    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        
        request.setCharacterEncoding("UTF-8");
        String userId = request.getParameter("user_id");
        String password = request.getParameter("user_pw");

        JSONObject jsonResponse = new JSONObject();
        response.setContentType("application/json; charset=UTF-8");

        if (userId == null || userId.trim().isEmpty() || password == null || password.isEmpty()) {
            response.setStatus(HttpServletResponse.SC_BAD_REQUEST);
            jsonResponse.put("status", "error");
            jsonResponse.put("message", "아이디와 비밀번호를 모두 입력해주세요.");
            response.getWriter().write(jsonResponse.toJSONString());
            return;
        }

        try {
            Long uId = loginSrvc.authenticateAndGetUid(userId, password);

            // --- DIAGNOSTIC LOG ---
            System.out.println("--- [SERVLET DIAGNOSIS] ---");
            System.out.println("uId returned from service: " + uId);
            if (uId != null) {
                System.out.println("Type of uId: " + uId.getClass().getName());
                System.out.println("Condition (uId != null) is TRUE.");
            } else {
                System.out.println("Condition (uId != null) is FALSE.");
            }
            System.out.println("--------------------------");

            if (uId != null) {
                HttpSession session = request.getSession();
                session.setAttribute("user", userId);
                session.setAttribute("u_id", uId);
                
                jsonResponse.put("status", "success");
                jsonResponse.put("message", "로그인 성공");
            } else {
                jsonResponse.put("status", "fail");
                jsonResponse.put("message", "아이디 또는 비밀번호가 일치하지 않습니다.");
            }
        } catch (Exception e) {
            // 데이터베이스 오류 등 예외 처리
            e.printStackTrace();
            response.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
            jsonResponse.put("status", "error");
            jsonResponse.put("message", "로그인 처리 중 오류가 발생했습니다.");
        }
        
        response.getWriter().write(jsonResponse.toJSONString());
    }
}
