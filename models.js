const { Sequelize, DataTypes } = require("sequelize");

// 데이터베이스 연결 (데이터베이스 이름, 유저이름, 비밀번호 설정해야함 > 설정완료)
const sequelize = new Sequelize("lotto_db", "lotto", "password", {
  host: "localhost",
  dialect: "postgres",
});

// 판매점 모델 정의
const LottoStore = sequelize.define("LottoStore", {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
  },
  name: {
    type: DataTypes.STRING(100),
    allowNull: false,
  },
  address: {
    type: DataTypes.STRING(255),
    allowNull: false,
  },
  phone: {
    type: DataTypes.STRING(30),
    allowNull: true,
  },
  lat: {
    type: DataTypes.DECIMAL(10, 6),
    allowNull: true, // 위도 정보가 항상 있지 않을 수도 있으므로 allowNull을 true로 설정할 수 있습니다.
  },
  lon: {
    type: DataTypes.DECIMAL(10, 6),
    allowNull: true, // 경도 정보도 마찬가지로 항상 있지 않을 수 있습니다.
  },
  first_prize: {
    type: DataTypes.INTEGER,
    allowNull: true,
    defaultValue: 0,
  },
  second_prize: {
    type: DataTypes.INTEGER,
    allowNull: true,
    defaultValue: 0,
  },
  score: {
    type: DataTypes.INTEGER,
    allowNull: true,
    defaultValue: 0,
  },
});

// 당첨 정보 모델 정의
const WinningInfo = sequelize.define("WinningInfo", {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true,
  },

  store_id: {
    type: DataTypes.INTEGER,
    allowNull: false,
    references: {
      model: LottoStore,
      key: "id",
    },
  },

  draw_no: {
    type: DataTypes.INTEGER,
    allowNull: false,
  },
  rank: {
    type: DataTypes.INTEGER,
    allowNull: false,
  },
  category: {
    type: DataTypes.STRING(10),
    allowNull: true,
  },
});

// 모델 간의 관계 설정 (이 부분 다시 체크하기)
LottoStore.hasMany(WinningInfo, { foreignKey: "store_id" });
WinningInfo.belongsTo(LottoStore, { foreignKey: "store_id" });

module.exports = {
  sequelize,
  LottoStore,
  WinningInfo,
};
