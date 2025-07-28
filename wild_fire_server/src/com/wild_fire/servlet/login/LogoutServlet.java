package com.wild_fire.servlet.login;

import com.wild_fire.DAO.UserDAO;

import javax.servlet.*;
import javax.servlet.http.*;
import javax.servlet.annotation.*;
import java.io.IOException;

@WebServlet("/logout")
public class LogoutServlet extends HttpServlet {
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        HttpSession session = req.getSession(false);
        if (req.getSession().getAttribute("user") != null) {
            session.invalidate();
        }
        // 로그아웃 후 결과 반환 (json, 페이지 이동 등 선택)
        resp.setContentType("application/json; charset=UTF-8");
        resp.getWriter().write("{\"result\":\"logout\"}");

    }
}