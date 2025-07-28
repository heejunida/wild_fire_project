package com.wild_fire.servlet.login;

import com.wild_fire.DAO.UserDAO;

import javax.servlet.http.*;
import java.io.IOException;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;

@WebServlet("/login")
public class LoginServlet extends HttpServlet {
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        req.setCharacterEncoding("UTF-8");
        String id = req.getParameter("user_id");
        String pw = req.getParameter("user_pw");

        UserDAO dao = new UserDAO();
        Long uId = dao.loginAndGetUid(id, pw);

        resp.setContentType("application/json; charset=UTF-8");
        if (uId != null) {
            HttpSession session = req.getSession();
            session.setAttribute("user", id);    // (String) user_id
            session.setAttribute("u_id", uId);   // (Long) u_id (PK)
            resp.getWriter().write("{\"result\":\"success\"}");
        } else {
            resp.getWriter().write("{\"result\":\"fail\"}");
        }
    }
}
